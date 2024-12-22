import psycopg2
from psycopg2 import sql
from be.model import error

class BookStoreSearcher:
    def __init__(self, dbname='bookstore', user='postgres', password='2792636748', host='localhost', port='5432'):
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.conn.autocommit = True  # 自动提交事务

    def store_id_exist(self, store_id):
        with self.conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT 1 FROM stores WHERE store_id = %s"), [store_id])
            return cur.fetchone() is not None

    def search_books(self, keyword, search_scope='all', search_in_store=False, store_id=None):
        match_query = []
        params = []

        if search_in_store and store_id is not None:
            if not self.store_id_exist(store_id):
                return error.error_store_not_found(store_id)

            try:
                with self.conn.cursor() as cur:
                    cur.execute(sql.SQL("SELECT book_id FROM stores WHERE store_id = %s"), [store_id])
                    book_ids = [row[0] for row in cur.fetchall()]
            except psycopg2.Error as e:
                return error.db_operation_error(e)

            if search_scope == 'all':
                fields = ['title', 'tags', 'content', 'book_intro']
                conditions = [sql.SQL(f"to_tsvector({field}) @@ to_tsquery(%s)") for field in fields]
                match_query.append(sql.SQL(" OR ").join(conditions))
                match_query.append(sql.SQL("id = ANY(%s)"))
                params = [keyword] * len(fields) + [book_ids]
            else:
                scopes = search_scope.split(' ')
                conditions = [sql.SQL(f"to_tsvector({scope}) @@ to_tsquery(%s)") for scope in scopes]
                match_query.append(sql.SQL(" OR ").join(conditions))
                match_query.append(sql.SQL("id = ANY(%s)"))
                params = [keyword] * len(scopes) + [book_ids]

        else:
            if search_scope == 'all':
                fields = ['title', 'tags', 'content', 'book_intro']
                conditions = [sql.SQL(f"to_tsvector({field}) @@ to_tsquery(%s)") for field in fields]
                match_query.append(sql.SQL(" OR ").join(conditions))
                params = [keyword] * len(fields)
            else:
                scopes = search_scope.split(' ')
                conditions = [sql.SQL(f"to_tsvector({scope}) @@ to_tsquery(%s)") for scope in scopes]
                match_query.append(sql.SQL(" OR ").join(conditions))
                params = [keyword] * len(scopes)

        query = sql.SQL("SELECT * FROM books WHERE ") + sql.SQL(" AND ").join(match_query)
        query = query + sql.SQL(" ORDER BY title")

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                results = cur.fetchall()
                if not results:
                    if not search_in_store:
                        return error.error_book_not_found(keyword)
                    else:
                        return error.error_book_not_found_in_the_store(keyword, store_id)

                books = []
                for row in results:
                    book = {
                        'id': row[0],
                        'title': row[1],
                        'tags': row[2],
                        'content': row[3],
                        'book_intro': row[4]
                    }
                    books.append(book)

                for book in books:
                    with self.conn.cursor() as cur:
                        cur.execute(sql.SQL("SELECT store_id FROM stores WHERE book_id = %s"), [book['id']])
                        store_info = cur.fetchone()
                        book['store_id'] = store_info[0] if store_info else 'Unknown Shop'

                return 200, books

        except psycopg2.Error as e:
            # 打印详细的错误信息以帮助调试
            # print(f"Database operation error: {e}")
            return error.db_operation_error(e)

    def close(self):
        if self.conn:
            self.conn.close()

# bss = BookStoreSearcher()
# code = self.searcher.search_books(
        #     keyword=self.keyword,
        #     search_scope="title tags",
        #     search_in_store=False
        # )
# code, results = bss.search_books("美丽心灵", "all", False)
# print(code)