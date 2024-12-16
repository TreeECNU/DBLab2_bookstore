from flask import Blueprint
from flask import request
from flask import jsonify
from be.model import search

bp_search = Blueprint("search", __name__, url_prefix="/search")

@bp_search.route("/search_books", methods=["POST"])
def search_books():
    keyword = request.json.get("keyword")
    search_scope = request.json.get("search_scope", "all")
    search_in_store = request.json.get("search_in_store", False)
    store_id = request.json.get("store_id", None)

    manager = search.BookStoreSearcher()
    code, results = manager.search_books(keyword, search_scope, search_in_store, store_id)

    return jsonify({"message": results}), code