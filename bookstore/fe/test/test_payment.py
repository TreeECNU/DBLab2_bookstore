import pytest

from fe.access.buyer import Buyer
from fe.access.seller import Seller
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.access.book import Book
import uuid


class TestPayment:
    seller_id: str
    store_id: str
    buyer_id: str
    password: str
    buy_book_info_list: [Book] # type: ignore
    total_price: int
    order_id: str
    buyer: Buyer
    seller:Seller

    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_payment_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_payment_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_payment_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        gen_book = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list = gen_book.gen(
            non_exist_book_id=False, low_stock_level=False, max_book_count=5
        )
        self.buy_book_info_list = gen_book.buy_book_info_list
        assert ok
        b = register_new_buyer(self.buyer_id, self.password)
        self.buyer = b
        self.seller=gen_book.seller
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
        yield

    def test_ok(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200

    def test_authorization_error(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        self.buyer.password = self.buyer.password + "_x"
        code = self.buyer.payment(self.order_id)
        assert code == 401

    def test_not_suff_funds(self):
        code = self.buyer.add_funds(self.total_price - 1)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 519

    def test_repeat_pay(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200

        code = self.buyer.payment(self.order_id)
        assert code == 527

    def test_order_is_exist(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        
        self.order_id = self.order_id + "_x"

        code = self.buyer.payment(self.order_id)
        assert code == 518

    def test_pay_order_id_is_equal(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        
        self.buyer.user_id = self.buyer.user_id + "_x"
        
        code = self.buyer.payment(self.order_id)
        assert code == 401

    def test_ship_order(self):
        code= self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)

        code = self.seller.ship(self.seller_id, self.store_id, self.order_id)
        assert code == 200

    def test_ship_order_non_existent_user(self):
        code= self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        code = self.seller.ship("non_existent_user", self.store_id, self.order_id)
        assert code == 511

    def test_ship_order_non_existent_store(self):
        code= self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        code = self.seller.ship(self.seller_id, "non_existent_store", self.order_id)
        assert code == 513

    def test_ship_order_non_existent_order(self):
        code= self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        code = self.seller.ship(self.seller_id, self.store_id, "non_existent_order")
        assert code == 518

    def test_repeat_ship_order(self):
        code= self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        
        code = self.seller.ship(self.seller_id, self.store_id, self.order_id)
        assert code == 200

        code = self.seller.ship(self.seller_id, self.store_id, self.order_id)
        assert code == 529
    
    def test_not_paid_ship(self):
        code = self.seller.ship(self.seller_id, self.store_id, self.order_id)
        assert code == 520