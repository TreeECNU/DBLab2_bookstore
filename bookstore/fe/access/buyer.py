import requests
import simplejson
from urllib.parse import urljoin
from fe.access.auth import Auth


class Buyer:
    def __init__(self, url_prefix, user_id, password):
        self.url_prefix = urljoin(url_prefix, "buyer/")
        self.user_id = user_id
        self.password = password
        self.token = ""
        self.terminal = "my terminal"
        self.auth = Auth(url_prefix)
        code, self.token = self.auth.login(self.user_id, self.password, self.terminal)
        assert code == 200

    def new_order(self, store_id: str, book_id_and_count: [(str, int)]) -> (int, str): # type: ignore
        books = []
        for id_count_pair in book_id_and_count:
            books.append({"id": id_count_pair[0], "count": id_count_pair[1]})
        json = {"user_id": self.user_id, "store_id": store_id, "books": books}
        url = urljoin(self.url_prefix, "new_order")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        return r.status_code, response_json.get("order_id")

    def payment(self, order_id: str) -> int:
        json = {"user_id": self.user_id, "order_id": order_id,"password": self.password}
        url = urljoin(self.url_prefix, "pay_to_platform")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def confirm_receipt_and_pay_to_seller(self, order_id: str) -> int:
        json = {"user_id": self.user_id, "order_id": order_id,"password": self.password}
        url = urljoin(self.url_prefix, "confirm_receipt_and_pay_toseller")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def add_funds(self, add_value: str) -> int:
        json = {
            "user_id": self.user_id,
            "password": self.password,
            "add_value": add_value,
        }
        url = urljoin(self.url_prefix, "add_funds")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    # 查询订单状态
    def query_order_status(self, order_id: str, user_id: str, password: str) -> (int, str, list): # type: ignore
        json = {"user_id": user_id, "order_id": order_id, "password": password}
        url = urljoin(self.url_prefix, "query_order_status")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        return response_json.get("code"), response_json.get("message"), response_json.get("order_status")

    # 查询用户所有订单
    def query_buyer_all_orders(self, user_id: str, password: str) -> (int, str, list): # type: ignore
        json = {"user_id": user_id, "password": password}
        url = urljoin(self.url_prefix, "query_buyer_all_orders")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        return response_json.get("code"), response_json.get("message"), response_json.get("orders")


    # 取消订单
    def cancel_order(self, order_id: str, user_id: str, password: str) -> (int, str): # type: ignore
        json = {"user_id": user_id, "order_id": order_id, "password": password}
        url = urljoin(self.url_prefix, "cancel_order")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        return response_json.get("code"), response_json.get("message")

    # 自动取消超时订单
    def auto_cancel_expired_orders(self) -> (int, str): # type: ignore
        url = urljoin(self.url_prefix, "auto_cancel_expired_orders")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers)
        response_json = r.json()
        return response_json.get("code"), response_json.get("message")

  