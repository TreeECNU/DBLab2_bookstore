import pytest
import concurrent.futures
import psycopg2
import uuid
import json
import logging
from fe.access.order_api import OrderAPI
from datetime import datetime, timedelta
from fe.access.auth import Auth
from fe import conf
from fe.access import seller, book

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

class TestBuyer:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.auth = Auth(conf.URL)

        # 创建测试用户
        self.user_id = f"test_user_{uuid.uuid1()}"
        self.password = "test_password"
        code = self.auth.register(self.user_id, self.password)
        assert code == 200

        self.order_api = OrderAPI(conf.URL, self.user_id, self.password)

        self.seller = seller.Seller(conf.URL, self.user_id, self.password)

        # 创建测试商店
        self.store_id = f"test_store_{uuid.uuid1()}"
        code = self.seller.create_store(self.store_id)
        assert code == 200

        # 添加测试书籍
        self.book_id = "1000067"
        book_db = book.BookDB(conf.Use_Large_DB)
        self.books = book_db.get_book_info(0, 2)
        self.book_json_str = self.books[0]
        self.stock_level = 10
        code = self.seller.add_book(self.store_id, self.stock_level, self.book_json_str)
        assert code == 200

        yield

    def test_concurrent_new_order(self):

        # 创建多个订单
        num_orders = 5
        id_and_count = [(self.book_id, 2)]

        def create_order(_):
            order_id = ""
            try:
                code, order_id = self.order_api.new_order(self.store_id, id_and_count)
                assert code == 200
            except Exception as e:
                logging.error(f"Error creating order: {e}")
            return order_id

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_orders) as executor:
            order_ids = list(executor.map(create_order, range(num_orders)))

        # 检查库存是否正确
        code, now_stock_level, _ = self.order_api.check_stock_level(self.store_id, self.book_id)
        expected_stock_level = self.stock_level - num_orders * id_and_count[0][1]
        assert code == 200
        assert now_stock_level == expected_stock_level

        # 检查订单数量是否正确
        code, order_count, _ = self.order_api.check_order_count(self.user_id)
        assert code == 200
        assert order_count == num_orders

    def test_concurrent_new_order_with_error_rollback(self):
        # 创建多个订单
        num_orders = 5
        id_and_count = [(self.book_id, 2)]

        def create_order(index):
            order_id = ""
            try:
                if index == 2:  # 故意让第三个订单创建失败
                    error_store_id = "error_store_id"
                    code, order_id = self.order_api.new_order(error_store_id, id_and_count)
                    assert code != 200
                else:
                    code, order_id = self.order_api.new_order(self.store_id, id_and_count)
                    assert code == 200
                
            except Exception as e:
                logging.error(f"Error creating order: {e}")
            return order_id

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_orders) as executor:
            order_ids = list(executor.map(create_order, range(num_orders)))

        # 检查库存是否正确
        code, now_stock_level, _ = self.order_api.check_stock_level(self.store_id, self.book_id)
        expected_stock_level = self.stock_level - (num_orders - 1) * id_and_count[0][1]  # 只有4个订单成功
        assert code == 200
        assert now_stock_level == expected_stock_level

        # 检查订单数量是否正确
        code, order_count, _ = self.order_api.check_order_count(self.user_id)
        assert code == 200
        assert order_count == num_orders - 1  # 只有4个订单成功
