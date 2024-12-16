## 搜索书籍

#### 首先是路由的实现：
```
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
```
from pymongo import MongoClient, TEXT
from pymongo.errors import PyMongoError
from be.model import error
```
然后定义一个BookStoreSearcher类：
1. 初始化  
所做的操作分别是：  
-  连接MongoDB数据库
-  连接到bookstore数据库
-  分别读取books表以及store表
-  删除所有存在的索引（这是为了后面能够成功创建索引）
-  创建全文索引
```
class BookStoreSearcher:
    def __init__(self, connection_string="mongodb://localhost:27017/", dbname='bookstore'):
        self.client = MongoClient(connection_string)
        self.db = self.client[dbname]
        self.booksdb = self.db['books']
        self.storedb = self.db['store']
        self.delete_all_indexes()
        self.ensure_text_index_exists()
```
2. 删除所有索引的实现  
注意这里的`# pragma: no cover`，这是因为数据库本身的错误很难去test，因此加入这行代码表示不测试数据库本身操作出错，下面也有这类问题，统一在此说明。
```
    def delete_all_indexes(self):
        try:
            self.booksdb.drop_indexes()
            print("All indexes deleted successfully.")
        except PyMongoError as e: # pragma: no cover
            print(f"An error occurred while deleting all indexes: {e}")
```
3. 创建全文索引
-  创建的索引名为`text_idx`，包含了四个字段：`title`、`tags`、`content`、`book_intro`。
-  每个字段的数据类型均被指定为`TEXT`，表明它们将被用作全文搜索的索引。全文搜索索引允许对文本内容进行更复杂的查询，比如基于关键词的搜索等，这里查询书籍就是使用了基于关键词的搜索。
```
    def ensure_text_index_exists(self):
        try:
            self.booksdb.create_index(
                    [('title', TEXT), ('tags', TEXT), ('content', TEXT), ('book_intro', TEXT)],
                    name='text_idx')
        except PyMongoError as e: # pragma: no cover
            print(f"An error occurred while ensuring the text index exists: {e}")
```
4. 查询store_id是否存在
这一步很重要，在后续的搜索中，如果指定了在某个store中进行搜索，但是该store_id查询不到会对结果有所影响。
```
    def store_id_exist(self, store_id):
        return self.storedb.find_one({"store_id": store_id}) is not None
```
5. 查询函数的具体实现
传入的四个参数如下：  

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
keyword | string | 搜索关键词 | N
search_scope | string | 搜索范围，可以是多个字段如'title tags'	也可以是全局搜索'all' | Y，默认为'all'
search_in_store | boolean | 是否只在指定店铺内搜索 | Y，默认为false
store_id | string | 店铺ID，仅当search_in_store为true时需要 | Y，默认为null

然后记录下所有的查询条件存放在match_query中（因为查询条件可能会很多）
```
    def search_books(self, keyword, search_scope='all', search_in_store=False, store_id=None):
        match_query = {}
```
6. 分情况讨论  
大情况一：如果选定了要在店铺搜索，并且指定了store_id：  
-  小情况1：如果store_id不存在，则返回第一个错误。（具体的错误以及错误码在后面介绍，下面不再赘述）
-  小情况2：将store表中该store_id对应的book_id都取出来。
-  小情况3：如果搜索条件为全文搜索，那么使用`$text`操作符来搜索关键字`keyword`，同时要求匹配文档的`id`必须存在于`book_ids`列表中，表示只搜索特定店铺内的存在的书籍。
-  小情况4：如果搜索条件为部分字段，创建一个条件列表，其中将多个搜索条件进行拆分，使用正则表达式进行匹配，并且不区分大小写，依次遍历每一个搜索条件。
```
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
```
大情况二：直接采用关键字搜索的方式搜索books表  
其中细分的两种小情况也都是和大情况一中的小情况34一样：  
-  小情况1：如果搜索条件为全文搜索，那么使用`$text`操作符来搜索关键字`keyword`。
-  小情况2：如果搜索条件为部分字段，创建一个条件列表，其中将多个搜索条件进行拆分，使用正则表达式进行匹配，并且不区分大小写，依次遍历每一个搜索条件。
```
        else:
            if search_scope == 'all':
                match_query['$text'] = {'$search': keyword}
            else:
                conditions = [{scope: {'$regex': keyword, '$options': 'i'}} for scope in search_scope.split(' ')]
                match_query['$or'] = conditions
```
7. 使用聚合管道pipeline：
-  `$match`阶段：过滤输入文档流，确保只有符合条件的文档通过。
-  `$lookup`阶段，进行`store`表和`books`表的关联查询，通过`store`表中的`book_id`和`books`表中的`id`进行关联。并且将结果存储在`store_info`中。  
-  `$addFields`阶段，第一个确保`store_info`字符按至少是一个数组，即使是空的；第二个是用于提取`store_info`中的第一个元素`store_id`，将其赋值为当前文档的`store_id`字段；如果`store_info`中的第一个元素`store_id`为空，则被设置为`Unknown Shop`。
-  `$project`阶段，在最终输出的文档中，排除`picture`、`store_info`和`_id`字段。
```
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
```
8. 进行最终查询，如果没有找到结果，那么根据是否在店铺中寻找返回不同的错误；如果找到了结果，返回正确的码200以及相应的results。
```
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
```
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
```
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