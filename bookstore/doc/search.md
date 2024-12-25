### 搜索书籍

因为这一块的函数逻辑比较复杂，所以详细解读如下：

#### 首先是路由的实现：
```Python
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
```
#### 路由的代码解读如下：

#### URL：
POST http://[address]/search/search_books

#### Request

##### Header:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "keyword": "关键词",
  "search_scope": "搜索范围",
  "search_in_store": "True or False",
  "store_id": "商店ID"
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
keyword | string | 搜索关键词 | N
search_scope | string | 搜索范围，可以是多个字段如'title tags'	也可以是全局搜索'all' | Y，默认为'all'
search_in_store | boolean | 是否只在指定店铺内搜索 | Y，默认为false
store_id | string | 店铺ID，仅当search_in_store为true时需要 | Y，默认为null

##### 具体搜索函数实现代码如下：  
首先导入相关的库：
```Python
import psycopg2
from psycopg2 import sql
from be.model import error
from pymongo import MongoClient
```
然后定义一个BookStoreSearcher类：
1. 初始化  
所做的操作分别是：  
-  连接MongoDB数据库
-  连接PostgreSQL数据库
-  连接到bookstore数据库
-  分别读取books表以及store表
-  创建全文索引
```Python
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
        self.mongo_client = MongoClient('mongodb://localhost:27017/')
        self.mongo_db = self.mongo_client['bookstore_pic']
        self.mongo_collection = self.mongo_db['books']

        # 创建索引
        self._create_indexes()
```
2. 创建全文索引
-  创建的索引名为`text_idx`，包含了四个字段：`title`、`tags`、`content`、`book_intro`。
-  它们将被用作全文搜索的索引。全文搜索索引允许对文本内容进行更复杂的查询，比如基于关键词的搜索等，这里查询书籍就是使用了基于关键词的搜索。【这里使用的是'english'，因为postgreSQL支持原生的english分词，那么如果要使用中文分词，需要使用'chinese'，需要额外安装zhparser，windows不太适合安装，linux安装更为合适】后续会详细介绍全文索引。
```Python
    def _create_indexes(self):
        """
        创建必要的索引以优化查询性能
        """
        with self.conn.cursor() as cur:
            # 在 stores 表的 store_id 列上创建索引
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_stores_store_id ON stores(store_id);
            """)

            # 在 books 表的 id 列上创建索引
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_books_id ON books(id);
            """)

            # 在 books 表的 title 列上创建全文搜索索引
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_books_title_fts ON books USING gin(to_tsvector('english', title));
            """)

            # 在 books 表的 tags 列上创建全文搜索索引
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_books_tags_fts ON books USING gin(to_tsvector('english', tags));
            """)

            # 在 books 表的 content 列上创建全文搜索索引
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_books_content_fts ON books USING gin(to_tsvector('english', content));
            """)

            # 在 books 表的 book_intro 列上创建全文搜索索引
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_books_book_intro_fts ON books USING gin(to_tsvector('english', book_intro));
            """)
```
3. 查询store_id是否存在
这一步很重要，在后续的搜索中，如果指定了在某个store中进行搜索，但是该store_id查询不到会对结果有所影响。
```Python
    def store_id_exist(self, store_id):
        with self.conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT 1 FROM stores WHERE store_id = %s"), [store_id])
            return cur.fetchone() is not None
```
4. 查询函数的具体实现
传入的四个参数如下：  

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
keyword | string | 搜索关键词 | N
search_scope | string | 搜索范围，可以是多个字段如'title tags'	也可以是全局搜索'all' | Y，默认为'all'
search_in_store | boolean | 是否只在指定店铺内搜索 | Y，默认为false
store_id | string | 店铺ID，仅当search_in_store为true时需要 | Y，默认为null

然后记录下所有的查询条件存放在match_query中（因为查询条件可能会很多）
```Python
    def search_books(self, keyword, search_scope='all', search_in_store=False, store_id=None):
        match_query = []
```
5. 分情况讨论  
大情况一：如果选定了要在店铺搜索，并且指定了store_id：  
-  小情况1：如果store_id不存在，则返回第一个错误。（具体的错误以及错误码在后面介绍，下面不再赘述）
-  小情况2：将store表中该store_id对应的book_id都取出来。
-  小情况3：如果搜索条件为全文搜索，那么使用`$text`操作符来搜索关键字`keyword`，同时要求匹配文档的`id`必须存在于`book_ids`列表中，表示只搜索特定店铺内的存在的书籍。
-  小情况4：如果搜索条件为部分字段，创建一个条件列表，其中将多个搜索条件进行拆分，使用正则表达式进行匹配，并且不区分大小写，依次遍历每一个搜索条件。
```Python
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
```
大情况二：直接采用关键字搜索的方式搜索books表  
其中细分的两种小情况也都是和大情况一中的小情况34一样：  
-  小情况1：如果搜索条件为全文搜索，那么使用`$text`操作符来搜索关键字`keyword`。
-  小情况2：如果搜索条件为部分字段，创建一个条件列表，其中将多个搜索条件进行拆分，使用正则表达式进行匹配，并且不区分大小写，依次遍历每一个搜索条件。
```Python
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
```
6. 进行最终查询，如果没有找到结果，那么根据是否在店铺中寻找返回不同的错误；如果找到了结果，返回正确的码200以及相应的results。
```Python
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

```
至此，搜索的代码已经解读完毕。

#### Response

Status Code:

码 | 描述
--- | ---
200 | 搜索成功
401 | 授权失败
523 | 书籍keyword不存在
524 | 店铺ID不存在
525 | 在指定店铺内未找到书籍keyword
530 | 数据库操作错误

##### Body:
```json
{
  "message": [搜索结果列表],
  "code": 状态码
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
message | array | 包含搜索结果的数组 | N
code    | integer | 响应状态码      | N

##### 测试文件如下：
注：代码注释已经囊括了该代码的含义，就不赘述了。
```Python
import pytest
from fe.access import book_search
from fe import conf

class TestSearchBooks:
    @pytest.fixture(autouse=True)
    def setup(self):
        # 初始化 bookstore_searcher 和相关数据
        self.store_id = "test_add_books_store_id_848aa78c-887a-11ef-89e5-2e81db39535e"
        self.keyword = "美丽心灵"
        self.searcher = book_search.BookSearcher(conf.URL)
        yield

    def test_non_exist_book_id_full(self):
        # 测试不存在的书籍，搜索是在book数据库中进行，搜索范围是全局，期望返回 523 错误码
        code = self.searcher.search_books(
            keyword="nonexistent_book",
            search_scope="all",
            search_in_store=False,
            store_id=self.store_id
        )
        assert code == 523
    
    def test_non_exist_book_id_part(self):
        # 测试不存在的书籍，搜索是在book数据库中进行，搜索范围是部分，期望返回 523 错误码
        code = self.searcher.search_books(
            keyword="nonexistent_book",
            search_scope="title tag",
            search_in_store=False,
            store_id=self.store_id
        )
        assert code == 523

    def test_non_exist_store_id(self):
        # 测试不存在的store_id，期望返回 524 错误码
        code = self.searcher.search_books(
            keyword=self.keyword,
            search_scope="all",
            search_in_store=True,
            store_id="non_existent_store_id"
        )
        assert code == 524

    def test_non_exist_book_id_in_the_store(self):
        # 测试书籍不存在store_id对应的store中，期望返回 525 错误码
        code = self.searcher.search_books(
            keyword="nonexistent_book",
            search_scope="all",
            search_in_store=True,
            store_id=self.store_id
        )
        assert code == 525

    def test_partial_scope_search(self):
        # 测试部分匹配 scope 搜索
        code = self.searcher.search_books(
            keyword=self.keyword,
            search_scope="title tags",
            search_in_store=False
        )
        assert code == 200

    def test_full_scope_search(self):
        # 测试全范围搜索
        code = self.searcher.search_books(
            keyword=self.keyword,
            search_scope="all",
            search_in_store=False
        )
        assert code == 200
    
    def test_full_scope_search_fail(self):
        # 测试全范围搜索，但是搜索失败
        code = self.searcher.search_books(
            keyword="nonexistent_book",
            search_scope="all",
            search_in_store=False
        )
        assert code == 523

    def test_search_books_in_existing_store(self):
        # 测试在存在的store_id中搜索书籍
        code = self.searcher.search_books(
            keyword=self.keyword,
            search_scope="all",
            search_in_store=True,
            store_id=self.store_id
        )
        assert code == 200
    
    def test_search_books_in_existing_store_part(self):
        # 测试在存在的store_id中搜索书籍，搜索范围是部分
        code = self.searcher.search_books(
            keyword=self.keyword,
            search_scope="title tag",
            search_in_store=True,
            store_id=self.store_id
        )
        assert code == 200
```

#### 前后端的连接函数代码如下：
用于解析前端发送的请求，然后再向后端进行发送，获取响应结果。
```Python
import requests
from urllib.parse import urljoin

class BookSearcher:
    def __init__(self, url_prefix):
        self.url_prefix = urljoin(url_prefix, "search/")
        self.token = ""

    def search_books(self, keyword: str, search_scope: str = "all", search_in_store: bool = False, store_id: str = None) -> (int, dict):
        """
        搜索书籍功能
        :param keyword: 搜索关键词
        :param search_scope: 搜索范围 (默认为 "all")
        :param search_in_store: 是否在特定商店中搜索 (默认为 False)
        :param store_id: 可选参数，指定商店 ID
        :return: 返回状态码和搜索结果
        """
        json_data = {
            "keyword": keyword,
            "search_scope": search_scope,
            "search_in_store": search_in_store
        }

        if store_id is not None:
            json_data["store_id"] = store_id

        url = urljoin(self.url_prefix, "search_books")
        headers = {"token": self.token} 
        response = requests.post(url, headers=headers, json=json_data)
        return response.status_code
```