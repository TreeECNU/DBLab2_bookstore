import psycopg2
import uuid
import json
import logging
from be.model import db_conn
from be.model import error
from datetime import datetime, timedelta
import schedule
import time
from psycopg2.extras import RealDictCursor



class Buyer(db_conn.DBConn):
    # 订单状态映射
    ORDER_STATUS = {
        "pending": "待支付",
        "paid": "已支付",
        "shipped": "已发货",
        "received": "已收货",
        "completed": "已完成",
        "canceled": "已取消"
    }

    def __init__(self):
        super().__init__()  # 初始化父类的数据库连接
    
    # def user_id_exist(self, user_id):
    #     try:
    #         with self.conn.cursor() as cursor:
    #             cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    #             return cursor.fetchone() is not None
    #     except Exception as e:
    #         logging.error(f"Error checking user_id_exist: {e}")
    #         return False

    # def store_id_exist(self, store_id):
    #     try:
    #         with self.conn.cursor() as cursor:
    #             cursor.execute("SELECT * FROM user_store WHERE store_id = %s", (store_id,))
    #             return cursor.fetchone() is not None
    #     except Exception as e:
    #         logging.error(f"Error checking store_id_exist: {e}")
    #         return False

    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)
            
            # 生成订单ID
            uid = f"{user_id}_{store_id}_{uuid.uuid1()}"

            # 遍历每本书籍及其数量
            for book_id, count in id_and_count:
                # 查找书籍库存
                with self.conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT stock_level, book_info 
                        FROM stores 
                        WHERE store_id = %s AND book_id = %s
                    """, (store_id, book_id))
                    store_item = cursor.fetchone()

                if store_item is None:
                    return error.error_non_exist_book_id(book_id) + (order_id,)
                
                stock_level, book_info_str = store_item
                book_info = json.loads(book_info_str)
                price = book_info.get("price")

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)
                
                # 更新库存
                with self.conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE stores 
                        SET stock_level = stock_level - %s 
                        WHERE store_id = %s AND book_id = %s AND stock_level >= %s
                    """, (count, store_id, book_id, count))
                    if cursor.rowcount == 0:
                        return error.error_stock_level_low(book_id) + (order_id,)
                
                # 插入订单详情
                with self.conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO new_order_details (order_id, book_id, count, price) 
                        VALUES (%s, %s, %s, %s)
                    """, (uid, book_id, count, price))
            
            # 插入订单，新增 is_shipped 和 is_received 初始为 False
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO new_orders (order_id, store_id, user_id, is_paid, is_shipped, is_received, order_completed, status, created_time) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (uid, store_id, user_id, False, False, False, False, "pending", datetime.utcnow()))
            
            self.conn.commit()
            order_id = uid
        except Exception as e:
            logging.error(f"Error creating new order: {e}")
            self.conn.rollback()
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    def pay_to_platform(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            # 查找订单
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM new_orders WHERE order_id = %s", (order_id,))
                order = cursor.fetchone()

            if order is None:
                return error.error_invalid_order_id(order_id)

            buyer_id = order[1]

            # 检查用户身份
            if buyer_id != user_id:
                return error.error_authorization_fail()

            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (buyer_id,))
                user = cursor.fetchone()

            if user is None or user[1] != password:
                return error.error_authorization_fail()
                

            # 检查是否已经付款
            if order[3]:
                return error.error_order_is_paid(order_id)

            # 计算订单总价
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT count, price FROM new_order_details WHERE order_id = %s", (order_id,))
                order_details = cursor.fetchall()

            total_price = sum(count * price for count, price in order_details)

            if user[2] < total_price:
                return error.error_not_sufficient_funds(order_id)

            # 扣除买家的余额，平台收款
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET balance = balance - %s 
                    WHERE user_id = %s AND balance >= %s
                """, (total_price, buyer_id, total_price))
                if cursor.rowcount == 0:
                    return error.error_not_sufficient_funds(order_id)

            # 更新订单状态为已付款
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE new_orders 
                    SET is_paid = %s 
                    WHERE order_id = %s
                """, (True, order_id))

            self.conn.commit()

        except Exception as e:
            logging.error(f"Error paying to platform: {e}")
            self.conn.rollback()
            return 530, "{}".format(str(e))

        return 200, "ok"

    def confirm_receipt_and_pay_to_seller(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            # 查找订单
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM new_orders WHERE order_id = %s", (order_id,))
                order = cursor.fetchone()

            buyer_id = order[1]

            # 检查用户身份
            if buyer_id != user_id:
                return error.error_authorization_fail()
            
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (buyer_id,))
                user = cursor.fetchone()

            if user is None or user[1] != password:
                return error.error_authorization_fail()
            
            # 检查是否已经付款
            if not order[3]:
                return error.error_not_be_paid(order_id)

            # 检查是否已确认收货
            if order[5]:
                return error.error_order_is_confirmed(order_id)

            buyer_id = order[1]
            store_id = order[2]

            with self.conn.cursor() as cursor:
                cursor.execute("SELECT user_id FROM user_store WHERE store_id = %s", (store_id,))
                seller = cursor.fetchone()
                seller_id = seller[0]

            # 计算订单总价
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT count, price FROM new_order_details WHERE order_id = %s", (order_id,))
                order_details = cursor.fetchall()

            total_price = sum(count * price for count, price in order_details)

            # 平台将钱转给卖家
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET balance = balance + %s 
                    WHERE user_id = %s
                """, (total_price, seller_id))

            # 更新订单状态为已确认收货
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE new_orders 
                    SET is_received = %s 
                    WHERE order_id = %s
                """, (True, order_id))

            # 更新订单状态为已完成
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE new_orders 
                    SET order_completed = %s 
                    WHERE order_id = %s
                """, (True, order_id))

            self.conn.commit()

        except Exception as e:
            logging.error(f"Error confirming receipt and paying to seller: {e}")
            self.conn.rollback()
            return 530, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()

            if user is None or user[1] != password:
                return error.error_authorization_fail()

            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users
                    SET balance = balance + %s 
                    WHERE user_id = %s
                """, (add_value, user_id))

            self.conn.commit()

        except Exception as e:
            logging.error(f"Error adding funds: {e}")
            self.conn.rollback()
            return 530, "{}".format(str(e))

        return 200, "ok"

    def query_order_status(self, user_id: str, order_id: str, password) -> (int, str, str):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)
            
            # 检查用户密码是否正确
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()

            if user is None or user[1] != password:
                return error.error_authorization_fail() + ("None",)

            # 查找订单
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM new_orders WHERE order_id = %s AND user_id = %s", (order_id, user_id))
                order = cursor.fetchone()

            if order is None:
                return error.error_invalid_order_id(order_id) + ("None",)

            # 返回订单状态
            order_status = self.ORDER_STATUS[order[7]]

            return 200, "ok", order_status
        except Exception as e:
            logging.error(f"Error querying order status: {e}")
            return 530, "{}".format(str(e)) + ("None",)

    def query_buyer_all_orders(self, user_id: str, password) -> (int, str, list):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)
            
            # 检查用户密码是否正确
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()

            if user is None or user[1] != password:
                return error.error_authorization_fail() + ("None",)

            # 查找用户的所有订单
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM new_orders WHERE user_id = %s", (user_id,))
                orders = cursor.fetchall()

            # 将查询结果转换为字典列表
            orders_list = [dict(zip([column[0] for column in cursor.description], row)) for row in orders]

            return 200, "ok", orders_list
        except Exception as e:
            logging.error(f"Error querying buyer all orders: {e}")
            return 530, "{}".format(str(e)), None

    def cancel_order(self, user_id: str, order_id: str, password) -> (int, str):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)

            # 检查用户密码是否正确
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()

            if user is None or user[1] != password:
                return error.error_authorization_fail()

            # 查找订单
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM new_orders WHERE order_id = %s AND user_id = %s", (order_id, user_id))
                order = cursor.fetchone()

            if order is None:
                return error.error_invalid_order_id(order_id)

            # 检查订单是否已经支付
            if order[3]:
                return error.error_cannot_be_canceled(order_id)

            # 取消订单，更新订单信息
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE new_orders 
                    SET status = %s 
                    WHERE order_id = %s
                """, ("canceled", order_id))

            # 恢复库存
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT book_id, count FROM new_order_details WHERE order_id = %s", (order_id,))
                order_details = cursor.fetchall()

            for book_id, count in order_details:
                with self.conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE stores 
                        SET stock_level = stock_level + %s 
                        WHERE store_id = %s AND book_id = %s
                    """, (count, order[1], book_id))

            self.conn.commit()

        except Exception as e:
            logging.error(f"Error canceling order: {e}")
            self.conn.rollback()
            return 530, "{}".format(str(e))

        return 200, "ok"

    def auto_cancel_expired_orders(self):
        try:
            # 获取当前时间
            now = datetime.utcnow()

            # 查找所有未支付的订单
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM new_orders WHERE is_paid = %s", (False,))
                pending_orders = cursor.fetchall()

            for order in pending_orders:
                created_time_str = order["created_time"]
                created_time = datetime.strptime(created_time_str, "%Y-%m-%d %H:%M:%S.%f")

                if created_time is not None:
                    time_diff = abs(now - created_time)

                    # 超时时间为5秒，检查订单是否已经超时
                    if time_diff > timedelta(seconds=5):
                        # 取消订单
                        order_id = order["order_id"]
                        with self.conn.cursor() as cursor:
                            cursor.execute("""
                                UPDATE new_orders 
                                SET status = %s 
                                WHERE order_id = %s
                            """, ("canceled", order_id))
                        
                        # 恢复库存
                        with self.conn.cursor() as cursor:
                            cursor.execute("SELECT book_id, count FROM new_order_details WHERE order_id = %s", (order_id,))
                            order_details = cursor.fetchall()

                        for book_id, count in order_details:
                            with self.conn.cursor() as cursor:
                                cursor.execute("""
                                    UPDATE stores 
                                    SET stock_level = stock_level + %s 
                                    WHERE store_id = %s AND book_id = %s
                                """, (count, order["store_id"], book_id))

            self.conn.commit()
        
        except Exception as e:
            logging.error(f"Error auto-canceling expired orders: {e}")
            self.conn.rollback()
            return 530, "not"
        
        return 200, "ok"