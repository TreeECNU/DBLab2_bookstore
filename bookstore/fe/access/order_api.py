import requests
from urllib.parse import urljoin
from fe.access.auth import Auth

class OrderAPI:
    def __init__(self, url_prefix, user_id, password):
        self.url_prefix = urljoin(url_prefix, "buyer/")
        self.user_id = user_id
        self.password = password
        self.token = ""

    def new_order(self, store_id: str, book_id_and_count: [(str, int)]) -> (int, str):
        books = []
        for id_count_pair in book_id_and_count:
            books.append({"id": id_count_pair[0], "count": id_count_pair[1]})
        json_data = {"user_id": self.user_id, "store_id": store_id, "books": books}
        url = urljoin(self.url_prefix, "new_order")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json_data)
        response_json = r.json()
        return r.status_code, response_json.get("order_id")
    def check_stock_level(self, store_id: str, book_id: str) -> (int, int, str):
        json = {"user_id": self.user_id, "store_id": store_id, "book_id": book_id}
        url = urljoin(self.url_prefix, "check_stock_level")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        return response_json.get("code"), response_json.get("stock_level"), response_json.get("message")
    
    def check_order_count(self, user_id: str) -> (int, int, str):
        json = {"user_id": user_id}
        url = urljoin(self.url_prefix, "check_order_count")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        return response_json.get("code"),response_json.get("order_count"), response_json.get("message")