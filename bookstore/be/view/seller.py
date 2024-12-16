from flask import Blueprint
from flask import request
from flask import jsonify
from be.model import seller
import json

bp_seller = Blueprint("seller", __name__, url_prefix="/seller")


@bp_seller.route("/create_store", methods=["POST"])
def seller_create_store():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    s = seller.Seller()
    code, message = s.create_store(user_id, store_id)
    return jsonify({"message": message}), code


@bp_seller.route("/add_book", methods=["POST"])
def seller_add_book():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_info: str = request.json.get("book_info")
    stock_level: str = request.json.get("stock_level", 0)

    s = seller.Seller()
    code, message = s.add_book(
        user_id, store_id, book_info.get("id"), json.dumps(book_info), stock_level
    )

    return jsonify({"message": message}), code

@bp_seller.route("/ship", methods=["POST"])
def ship():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    order_id: str = request.json.get("order_id")
    s = seller.Seller()
    code, message = s.ship(user_id, store_id,order_id)
    return jsonify({"message": message, "code": code})

@bp_seller.route("/add_stock_level", methods=["POST"])
def add_stock_level():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    book_id: str = request.json.get("book_id")
    add_num: str = request.json.get("add_stock_level", 0)

    s = seller.Seller()
    code, message = s.add_stock_level(user_id, store_id, book_id, add_num)

    return jsonify({"message": message}), code

@bp_seller.route("/query_one_store_orders", methods=["POST"])
def query_store_orders():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    password = request.json.get("password")

    s = seller.Seller()
    code, message, orders = s.query_one_store_orders(user_id, store_id, password)

    return jsonify({"message": message, "code": code, "orders": orders})


@bp_seller.route("/query_all_store_orders", methods=["POST"])
def query_all_store_orders():
    user_id: str = request.json.get("user_id")
    password = request.json.get("password")

    s = seller.Seller()
    code, message, orders = s.query_all_store_orders(user_id, password)

    return jsonify({"message": message, "code": code, "orders": orders})
