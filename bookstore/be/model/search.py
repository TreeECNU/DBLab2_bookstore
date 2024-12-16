from pymongo import MongoClient, TEXT
from pymongo.errors import PyMongoError
from be.model import error

class BookStoreSearcher:
    def __init__(self, connection_string="mongodb://localhost:27017/", dbname='bookstore'):
        self.client = MongoClient(connection_string)
        self.db = self.client[dbname]
        self.booksdb = self.db['books']
        self.storedb = self.db['store']
        self.delete_all_indexes()
        self.ensure_text_index_exists()
    
    def delete_all_indexes(self):
        try:
            self.booksdb.drop_indexes()
            print("All indexes deleted successfully.")
        except PyMongoError as e: # pragma: no cover
            print(f"An error occurred while deleting all indexes: {e}")

    def ensure_text_index_exists(self):
        try:
            # existing_indexes = self.booksdb.list_indexes()
            # text_index_found = any('text' in index['name'] for index in existing_indexes)
            # if not text_index_found:
            self.booksdb.create_index(
                    [('title', TEXT), ('tags', TEXT), ('content', TEXT), ('book_intro', TEXT)],
                    name='text_idx')
        except PyMongoError as e: # pragma: no cover
            print(f"An error occurred while ensuring the text index exists: {e}")

    def store_id_exist(self, store_id):
        return self.storedb.find_one({"store_id": store_id}) is not None

    def search_books(self, keyword, search_scope='all', search_in_store=False, store_id=None):
        match_query = {}

        if search_in_store and store_id is not None:
            if not self.store_id_exist(store_id):
                return error.error_store_not_found(store_id)

            try:
                book_ids = [book['book_id'] for book in self.storedb.find({'store_id': store_id})]
            except PyMongoError as e: # pragma: no cover
                return error.db_operation_error(e)

            if search_scope == 'all':
                match_query['$text'] = {'$search': keyword}
                match_query['id'] = {'$in': book_ids}
            else:
                conditions = [{scope: {'$regex': keyword, '$options': 'i'}} for scope in search_scope.split(' ')]
                match_query['$or'] = conditions
                match_query['id'] = {'$in': book_ids}

        else:
            if search_scope == 'all':
                match_query['$text'] = {'$search': keyword}
            else:
                conditions = [{scope: {'$regex': keyword, '$options': 'i'}} for scope in search_scope.split(' ')]
                match_query['$or'] = conditions

        pipeline = [
            {'$match': match_query},
            {'$lookup': {
                'from': 'store',
                'localField': 'id',
                'foreignField': 'book_id',
                'as': 'store_info'
            }},
            {'$addFields': {'store_info': {'$ifNull': ['$store_info', []]}}},
            {'$addFields': {'store_id': {'$ifNull': [{'$arrayElemAt': ['$store_info.store_id', 0]}, 'Unknown Shop']}}},
            {'$project': {'picture': 0, 'store_info': 0, '_id': 0}}
        ]

        try:
            results = list(self.booksdb.aggregate(pipeline))
            if not results:
                if not search_in_store:
                    return error.error_book_not_found(keyword)
                else:
                    return error.error_book_not_found_in_the_store(keyword, store_id)
            return 200, results
        except PyMongoError as e: # pragma: no cover
            return error.db_operation_error(e)

# searcher = BookStoreSearcher()
# # code, results = searcher.search_books('丑陋心灵', 'all', True, 'test_add_books_store_id_848aa78c-887a-11ef-89e5-2e81db39535e')
# code, results = searcher.search_books('美丽心灵', 'all')
# print(code)
# print(results)
