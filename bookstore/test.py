import unittest
import concurrent.futures
import psycopg2
import uuid
import json
import logging
from be.model import db_conn
from be.model import error
from be.model.buyer import Buyer
from be.model.seller import Seller
from be.model.user import User
from datetime import datetime, timedelta

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

class TestBuyer(unittest.TestCase):
    def setUp(self):
        # 初始化数据库连接
        self.conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="bookstore",
            user="postgres",
            password="2792636748"
        )
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

        # 初始化用户、商店和书籍
        self.user = User()
        self.seller = Seller()
        self.buyer = Buyer()

        # 创建测试用户
        self.user_id = "test_user"
        self.password = "test_password"
        self.user.register(self.user_id, self.password)

        # 创建测试商店
        self.store_id = "test_store"
        self.seller.create_store(self.user_id, self.store_id)

        # 添加测试书籍
        self.book_id = "test_book"
        self.book_json_str = '{"title": "Test Book", "tags": "test", "content": "This is a test book.", "book_intro": "Introduction to test book."}'
        self.stock_level = 10
        self.seller.add_book(self.user_id, self.store_id, self.book_id, self.book_json_str, self.stock_level)

    def tearDown(self):
        # 清理测试数据
        self.cursor.execute("DELETE FROM users WHERE user_id = %s", (self.user_id,))
        self.cursor.execute("DELETE FROM user_store WHERE store_id = %s", (self.store_id,))
        self.cursor.execute("DELETE FROM stores WHERE store_id = %s AND book_id = %s", (self.store_id, self.book_id))
        self.cursor.execute("DELETE FROM new_orders WHERE user_id = %s", (self.user_id,))
        self.cursor.execute("DELETE FROM new_order_details WHERE order_id IN (SELECT order_id FROM new_orders WHERE user_id = %s)", (self.user_id,))
        self.conn.commit()

        # 关闭数据库连接
        self.cursor.close()
        self.conn.close()

    def test_concurrent_new_order(self):
        # 创建多个订单
        num_orders = 5
        id_and_count = [(self.book_id, 2)]

        def create_order(_):
            order_id = ""
            try:
                buyer = Buyer()  # 每个线程创建自己的Buyer实例
                code, msg, order_id = buyer.new_order(self.user_id, self.store_id, id_and_count)
                self.assertEqual(code, 200)
            except Exception as e:
                logging.error(f"Error creating order: {e}")
            return order_id

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_orders) as executor:
            order_ids = list(executor.map(create_order, range(num_orders)))

        # 检查库存是否正确
        self.cursor.execute("SELECT stock_level FROM stores WHERE store_id = %s AND book_id = %s", (self.store_id, self.book_id))
        stock_level = self.cursor.fetchone()[0]
        expected_stock_level = self.stock_level - num_orders * id_and_count[0][1]
        self.assertEqual(stock_level, expected_stock_level)

        # 检查订单数量是否正确
        self.cursor.execute("SELECT COUNT(*) FROM new_orders WHERE user_id = %s", (self.user_id,))
        order_count = self.cursor.fetchone()[0]
        self.assertEqual(order_count, num_orders)

    # def test_concurrent_cancel_order(self):
    #     # 创建多个订单
    #     num_orders = 5
    #     id_and_count = [(self.book_id, 2)]

    #     order_ids = []
    #     for _ in range(num_orders):
    #         code, msg, order_id = self.buyer.new_order(self.user_id, self.store_id, id_and_count)
    #         self.assertEqual(code, 200)
    #         order_ids.append(order_id)

    #     def cancel_order(order_id):
    #         try:
    #             buyer = Buyer()  # 每个线程创建自己的Buyer实例
    #             code, msg = buyer.cancel_order(self.user_id, order_id, self.password)
    #             self.assertEqual(code, 200)
    #             logging.debug(f"Order {order_id} canceled successfully.")
    #         except Exception as e:
    #             logging.error(f"Error canceling order {order_id}: {e}")

    #     with concurrent.futures.ThreadPoolExecutor(max_workers=num_orders) as executor:
    #         list(executor.map(cancel_order, order_ids))

    #     # 检查库存是否恢复
    #     self.cursor.execute("SELECT stock_level FROM stores WHERE store_id = %s AND book_id = %s", (self.store_id, self.book_id))
    #     stock_level = self.cursor.fetchone()[0]
    #     self.assertEqual(stock_level, self.stock_level, f"Expected stock level {self.stock_level}, but got {stock_level}")

    #     # 检查订单状态是否为取消
    #     for order_id in order_ids:
    #         self.cursor.execute("SELECT status FROM new_orders WHERE order_id = %s", (order_id,))
    #         status = self.cursor.fetchone()[0]
    #         self.assertEqual(status, "canceled", f"Order {order_id} status should be 'canceled', but got {status}")

if __name__ == '__main__':
    unittest.main()