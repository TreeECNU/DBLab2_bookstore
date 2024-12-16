import psycopg2
from be.model import error
from be.model import db_conn


class Seller(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def add_book(
        self,
        user_id: str,
        store_id: str,
        book_id: str,
        book_json_str: str,
        stock_level: int,
    ):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            # 检查商店是否存在
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            # 检查书籍是否已经存在
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            # 将书籍插入到store表中
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO stores (store_id, book_id, book_info, stock_level)
                    VALUES (%s, %s, %s, %s)
                """, (store_id, book_id, book_json_str, stock_level))
                self.conn.commit()
        except Exception as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def add_stock_level(
        self, 
        user_id: str, 
        store_id: str, 
        book_id: str, 
        add_stock_level: int
    ):
        try:
            # 检查用户、商店和书籍是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            # 更新库存数量
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE stores
                    SET stock_level = stock_level + %s
                    WHERE store_id = %s AND book_id = %s
                """, (add_stock_level, store_id, book_id))
                self.conn.commit()
        except Exception as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            # 检查商店是否已经存在
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)

            # 创建商店，插入到user_store表中
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_store (store_id, user_id)
                    VALUES (%s, %s)
                """, (store_id, user_id))
                self.conn.commit()
        except Exception as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def ship(
            self,
            user_id: str,
            store_id: str,
            order_id: str,
            ):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            # 检查商店是否存在
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            # 检查订单是否存在
            if not self.order_id_exist(order_id):
                return error.error_invalid_order_id(order_id)
            # 检查订单是否已经支付
            if not self.order_is_paid(order_id):
                return error.error_not_be_paid(order_id)
            # 检查订单是否已经发货
            if self.order_is_shipped(order_id):
                return error.error_order_is_shipped(order_id)
            # 更新订单状态
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE new_orders
                    SET is_shipped = TRUE
                    WHERE order_id = %s AND store_id = %s
                """, (order_id, store_id))
                self.conn.commit()
        
        except Exception as e:
            return 520, "{}".format(str(e))
        return 200, "ok"

    def query_one_store_orders(self, user_id: str, store_id: str, password) -> (int, str, list):
        try:
            # 检查用户与商店是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + ("None",)
            
            # 检查用户密码是否正确
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT password FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()
                if not user or user[0] != password:
                    return error.error_authorization_fail() + ("None",)

                # 查找用户是否存在该商店
                cursor.execute("SELECT * FROM user_store WHERE user_id = %s AND store_id = %s", (user_id, store_id))
                user_store = cursor.fetchone()
                
                if not user_store:
                    return error.error_no_store_found(user_id) + ("None",)

                # 查找该商店的所有订单
                cursor.execute("SELECT * FROM new_orders WHERE store_id = %s", (store_id,))
                orders = cursor.fetchall()

        except Exception as e:
            return 530, "{}".format(str(e)), "None"
        return 200, "ok", [dict(zip([column[0] for column in cursor.description], row)) for row in orders]

    def query_all_store_orders(self, user_id: str, password) -> (int, str, list):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)

            # 检查用户密码是否正确
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT password FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()
                if not user or user[0] != password:
                    return error.error_authorization_fail() + ("None",)

                # 查找用户的商店
                cursor.execute("SELECT * FROM user_store WHERE user_id = %s", (user_id,))
                user_stores = cursor.fetchall()

                # 检查是否有商店
                if len(user_stores) == 0:
                    return error.error_no_store_found(user_id) + ("None",)

                all_store_orders = {}
                for user_store in user_stores:
                    store_id = user_store[1]
                    # 查找该商店的所有订单
                    cursor.execute("SELECT * FROM new_orders WHERE store_id = %s", (store_id,))
                    orders = cursor.fetchall()
                    all_store_orders[store_id] = [dict(zip([column[0] for column in cursor.description], row)) for row in orders]

        except Exception as e:
            return 530, "{}".format(str(e)), "None"
        return 200, "ok", all_store_orders

    # def user_id_exist(self, user_id: str) -> bool:
    #     try:
    #         with self.conn.cursor() as cursor:
    #             cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    #             return cursor.fetchone() is not None
    #     except Exception as e:
    #         return False

    # def store_id_exist(self, store_id: str) -> bool:
    #     try:
    #         with self.conn.cursor() as cursor:
    #             cursor.execute("SELECT * FROM user_store WHERE store_id = %s", (store_id,))
    #             return cursor.fetchone() is not None
    #     except Exception as e:
    #         return False

    # def book_id_exist(self, store_id: str, book_id: str) -> bool:
    #     try:
    #         with self.conn.cursor() as cursor:
    #             cursor.execute("SELECT * FROM stores WHERE store_id = %s AND book_id = %s", (store_id, book_id))
    #             return cursor.fetchone() is not None
    #     except Exception as e:
    #         return False

    # def order_id_exist(self, order_id: str) -> bool:
    #     try:
    #         with self.conn.cursor() as cursor:
    #             cursor.execute("SELECT * FROM new_orders WHERE order_id = %s", (order_id,))
    #             return cursor.fetchone() is not None
    #     except Exception as e:
    #         return False

    # def order_is_paid(self, order_id: str) -> bool:
    #     try:
    #         with self.conn.cursor() as cursor:
    #             cursor.execute("SELECT is_paid FROM new_orders WHERE order_id = %s", (order_id,))
    #             result = cursor.fetchone()

    #             return result and result[0]
    #     except Exception as e:
    #         return False

    # def order_is_shipped(self, order_id: str) -> bool:
    #     try:
    #         with self.conn.cursor() as cursor:
    #             cursor.execute("SELECT is_shipped FROM new_orders WHERE order_id = %s", (order_id,))
    #             result = cursor.fetchone()
    #             return result and result[0]
    #     except Exception as e:
    #         return False