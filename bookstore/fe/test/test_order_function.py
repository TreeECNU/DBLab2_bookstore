import pytest
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.book import Book
import uuid
import time

class TestOrderFunctions:
    seller_id: str
    store_id: str
    buyer_id: str
    buyer_password: str
    seller_password: str
    buy_book_info_list: [Book] # type: ignore
    total_price: int
    order_id: str
   
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_order_functions_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_order_functions_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_order_functions_buyer_id_{}".format(str(uuid.uuid1()))
        self.buyer_password = self.buyer_id

        gen_book = GenBook(self.seller_id, self.store_id)
        
        self.seller = gen_book.seller
        self.seller_password = self.seller.password
        
        ok, buy_book_id_list = gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        self.buy_book_info_list = gen_book.buy_book_info_list
        assert ok

        b = register_new_buyer(self.buyer_id, self.buyer_password)


        self.buyer = b
        code, self.order_id = b.new_order(self.store_id, buy_book_id_list)
        assert code == 200

        self.total_price = 0
        for item in self.buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is None:
                continue
            else:
                self.total_price = self.total_price + book.price * num


        self.order_lists = []
        self.seller_id_lists = []
        self.store_id_lists = []
        for i in range(5):
            seller_id = "test_order_functions_seller_id_{}_{}".format(str(uuid.uuid1()), i)
            store_id = "test_order_functions_store_id_{}_{}".format(str(uuid.uuid1()), i)
            gen_book = GenBook(seller_id, store_id)
            
            seller = gen_book.seller
    
            self.seller_id_lists.append(seller.seller_id)
            self.store_id_lists.append(store_id)
        
            ok, buy_book_id_list = gen_book.gen(
                non_exist_book_id=False, low_stock_level=False, max_book_count=i+1
            )
            assert ok
            
            code, order_id_test = b.new_order(store_id, buy_book_id_list)
            assert code == 200
            self.order_lists.append(order_id_test)

        yield


    def test_query_order_status_ok(self):
        # 查询成功
        code, _, _ = self.buyer.query_order_status(self.order_id, self.buyer_id, self.buyer_password)
        assert code == 200

    def test_query_buyer_all_orders_ok(self):
        # 查询成功
        code, _, _ = self.buyer.query_buyer_all_orders(self.buyer_id, self.buyer_password)
        assert code == 200

    def test_cancel_order_ok(self):
        # 取消成功
        code, _ = self.buyer.cancel_order(self.order_id, self.buyer_id, self.buyer_password)
        assert code == 200
    
    def test_query_order_status_fail(self):
        # 用户ID不存在
        user_id_test = self.buyer_id + "_x"
        code, _, _ = self.buyer.query_order_status(self.order_id, user_id_test, self.buyer_password)
        assert code == 511

        # 非法订单ID
        order_id_test = self.order_id + "_x"
        code, _, _ = self.buyer.query_order_status(order_id_test, self.buyer_id, self.buyer_password)
        assert code == 518

        # 授权失败
        password_test = self.buyer_password + "_x"
        code, _, _ = self.buyer.query_order_status(self.order_id, self.buyer_id, password_test)
        assert code == 401

    def test_query_buyer_all_orders_fail(self):
        # 用户ID不存在
        user_id_test = self.buyer_id + "_x"
        code, _, _ = self.buyer.query_buyer_all_orders(user_id_test, self.buyer_password)
        assert code == 511

        # 授权失败
        password_test = self.buyer_password + "_x"
        code, _, _ = self.buyer.query_buyer_all_orders(self.buyer_id, password_test)
        assert code == 401
    

    def test_cancel_order_fail(self):
        # 用户ID不存在
        user_id_test = self.buyer_id + "_x"
        code, _ = self.buyer.cancel_order(self.order_id, user_id_test, self.buyer_password)
        assert code == 511

        # 非法订单ID
        order_id_test = self.order_id + "_x"
        code, _ = self.buyer.cancel_order(order_id_test, self.buyer_id, self.buyer_password)
        assert code == 518

        # 授权失败
        password_test = self.buyer_password + "_x"
        code, _ = self.buyer.cancel_order(self.order_id, self.buyer_id, password_test)
        assert code == 401

        # 已支付，取消订单失败
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        code, _ = self.buyer.cancel_order(self.order_id, self.buyer_id, self.buyer_password)
        assert code == 521

    def test_auto_cancel_expired_orders(self):
        # 循环调用自动取消接口，每隔3秒一次，执行5次
        for _ in range(5):  
            code, message = self.buyer.auto_cancel_expired_orders()
            assert code == 200
            print(f"Auto cancel expired orders call result: {message}")
            time.sleep(2)  # 等待2秒

    def test_query_one_store_orders_ok(self):
        # 查询商铺订单信息成功
        code, _, _ = self.seller.query_one_store_orders(self.seller.seller_id, self.store_id, self.seller_password)
        assert code == 200

    def test_query_all_store_orders_ok(self):
        # 查询商铺订单信息成功
        code, _, _ = self.seller.query_all_store_orders(self.seller.seller_id, self.seller_password)
        assert code == 200

    def test_query_one_store_orders_fali(self):
        # 用户ID不存在
        seller_id_test = self.seller.seller_id+ "_x"
        code, _, _ = self.seller.query_one_store_orders(seller_id_test, self.store_id, self.seller_password)
        assert code == 511

        # 商铺ID不存在
        store_id_test = self.store_id + "_x"
        code, _, _ = self.seller.query_one_store_orders(self.seller.seller_id, store_id_test, self.seller_password)
        assert code == 513

        # 授权失败
        password_test = self.seller_password+ "_x"
        code, _, _ = self.seller.query_one_store_orders(self.seller.seller_id, self.store_id, password_test)
        assert code == 401

        # 卖家不存在该商铺
        code, _, _ = self.seller.query_one_store_orders(self.seller.seller_id, self.store_id_lists[2], self.seller_password)
        assert code == 522

    def test_query_all_store_orders_fail(self):
        # 用户ID不存在
        seller_id_test = self.seller.seller_id+ "_x"
        code, _, _ = self.seller.query_all_store_orders(seller_id_test, self.seller_password)
        assert code == 511

        # 授权失败
        password_test = self.seller_password+ "_x"
        code, _, _ = self.seller.query_all_store_orders(self.seller.seller_id, password_test)
        assert code == 401

        # 卖家不存在商铺
        code, _, _ = self.seller.query_all_store_orders(self.buyer_id, self.buyer_password)
        assert code == 522
        