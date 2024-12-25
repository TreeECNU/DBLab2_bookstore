### 创建商铺



#### URL

POST http://[address]/seller/create_store

#### Request
Headers:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

Body:

```json
{
  "user_id": "$seller id$",
  "store_id": "$store id$"
}
```

key | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 卖家用户ID | N
store_id | string | 商铺ID | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 创建商铺成功
514 | 商铺ID已存在

#### 对应测试代码
```python
    def test_ok(self):
        self.seller = register_new_seller(self.user_id, self.password)
        code = self.seller.create_store(self.store_id)
        assert code == 200

    def test_error_exist_store_id(self):
        self.seller = register_new_seller(self.user_id, self.password)
        code = self.seller.create_store(self.store_id)
        assert code == 200

        code = self.seller.create_store(self.store_id)
        assert code != 200

```

#### 对应后端实现代码

```Python
    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            # 检查商店是否已经存在
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)

            # 创建商店，插入到user_store表中
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_store (store_id, user_id)
                    VALUES (%s, %s)
                """, (store_id, user_id))
                self.conn.commit()
        except Exception as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
```

上述代码实现了一个创建商铺的功能，说明如下：

1. **检查用户是否存在**：
  - 调用 `self.user_id_exist(user_id)` 检查给定的 `user_id` 是否存在。
  - 如果用户不存在，返回错误信息 `error.error_non_exist_user_id(user_id)`。

2. **检查商店是否已经存在**：
  - 调用 `self.store_id_exist(store_id)` 检查给定的 `store_id` 是否已经存在。
  - 如果商店已存在，返回错误信息 `error.error_exist_store_id(store_id)`。

3. **创建商店**：
  - 使用数据库连接的游标执行 SQL 插入语句，将新的商店信息插入到 `user_store` 表中。
  - 插入的数据包括 `store_id` 和 `user_id`。
  - 提交事务以确保更改保存到数据库。

4. **异常处理**：
  - 如果在执行过程中发生任何异常，捕获异常并返回状态码 `530` 和异常信息。

5. **返回结果**：
  - 如果所有操作都成功完成，返回状态码 `200` 和消息 `"ok"`。


### 商家添加书籍信息

#### URL：
POST http://[address]/seller/add_book

#### Request
Headers:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

Body:

```json
{
  "user_id": "$seller user id$",
  "store_id": "$store id$",
  "book_info": {
    "tags": [
      "tags1",
      "tags2",
      "tags3",
      "..."
    ],
    "pictures": [
      "$Base 64 encoded bytes array1$",
      "$Base 64 encoded bytes array2$",
      "$Base 64 encoded bytes array3$",
      "..."
    ],
    "id": "$book id$",
    "title": "$book title$",
    "author": "$book author$",
    "publisher": "$book publisher$",
    "original_title": "$original title$",
    "translator": "translater",
    "pub_year": "$pub year$",
    "pages": 10,
    "price": 10,
    "binding": "平装",
    "isbn": "$isbn$",
    "author_intro": "$author introduction$",
    "book_intro": "$book introduction$",
    "content": "$chapter1 ...$"
  },
  "stock_level": 0
}

```

属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 卖家用户ID | N
store_id | string | 商铺ID | N
book_info | class | 书籍信息 | N
stock_level | int | 初始库存，大于等于0 | N

book_info类：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
id | string | 书籍ID | N
title | string | 书籍题目 | N
author | string | 作者 | Y
publisher | string | 出版社 | Y
original_title | string | 原书题目 | Y
translator | string | 译者 | Y
pub_year | string | 出版年月 | Y
pages | int | 页数 | Y
price | int | 价格(以分为单位) | N
binding | string | 装帧，精状/平装 | Y
isbn | string | ISBN号 | Y
author_intro | string | 作者简介 | Y
book_intro | string | 书籍简介 | Y
content | string | 样章试读 | Y
tags | array | 标签 | Y
pictures | array | 照片 | Y

tags和pictures：

    tags 中每个数组元素都是string类型  
    picture 中每个数组元素都是string（base64表示的bytes array）类型


#### Response

Status Code:

码 | 描述
--- | ---
200 | 添加图书信息成功
511 | 卖家用户ID不存在
513 | 商铺ID不存在
516 | 图书ID已存在

#### 对应测试代码
```python
    def test_ok(self):
        for b in self.books:
            code = self.seller.add_book(self.store_id, 0, b)
            assert code == 200

    def test_error_non_exist_store_id(self):
        for b in self.books:
            # non exist store id
            code = self.seller.add_book(self.store_id + "x", 0, b)
            assert code != 200

    def test_error_exist_book_id(self):
        for b in self.books:
            code = self.seller.add_book(self.store_id, 0, b)
            assert code == 200
        for b in self.books:
            # exist book id
            code = self.seller.add_book(self.store_id, 0, b)
            assert code != 200

    def test_error_non_exist_user_id(self):
        for b in self.books:
            # non exist user id
            self.seller.seller_id = self.seller.seller_id + "_x"
            code = self.seller.add_book(self.store_id, 0, b)
            assert code != 200

```

#### 对应后端实现代码

```Python
    def add_book(
        self,
        user_id: str,
        store_id: str,
        book_id: str,
        book_json_str: str,
        stock_level: int,
    ):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            # 检查商店是否存在
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            # 检查书籍是否已经存在
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            # 将书籍插入到store表中
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO stores (store_id, book_id, book_info, stock_level)
                    VALUES (%s, %s, %s, %s)
                """, (store_id, book_id, book_json_str, stock_level))
                self.conn.commit()
        except Exception as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
```

上述代码实现了一个商家添加书籍信息的功能，说明如下：

1. **检查用户是否存在**：
   - 使用 `self.user_id_exist(user_id)` 方法检查用户是否存在，如果不存在则返回错误信息。
   
2. **检查商店是否存在**：
   - 使用 `self.store_id_exist(store_id)` 方法检查商店是否存在，如果不存在则返回错误信息。
   
3. **检查书籍是否已经存在**：
   - 使用 `self.book_id_exist(store_id, book_id)` 方法检查书籍是否已经在该商店中存在，如果存在则返回错误信息。

4. **插入书籍信息**：
   - 如果上述检查都通过，则使用SQL语句将书籍信息插入到 `stores` 表中，并提交事务。

5. **异常处理**：
   - 如果在执行过程中发生任何异常，捕获异常并返回错误码530及异常信息。

6. **返回结果**：
   - 如果成功添加书籍，返回状态码200及"ok"消息。

### 商家添加书籍库存


#### URL

POST http://[address]/seller/add_stock_level

#### Request
Headers:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

Body:

```json
{
  "user_id": "$seller id$",
  "store_id": "$store id$",
  "book_id": "$book id$",
  "add_stock_level": 10
}
```
key | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 卖家用户ID | N
store_id | string | 商铺ID | N
book_id | string | 书籍ID | N
add_stock_level | int | 增加的库存量 | N

#### Response

Status Code:

码 | 描述
--- | :--
200 | 创建商铺成功
513 | 商铺ID不存在 
515 | 图书ID不存在 

#### 对应测试代码
```python
    def test_error_user_id(self):
        for b in self.books:
            book_id = b.id
            code = self.seller.add_stock_level(
                self.user_id + "_x", self.store_id, book_id, 10
            )
            assert code != 200

    def test_error_store_id(self):
        for b in self.books:
            book_id = b.id
            code = self.seller.add_stock_level(
                self.user_id, self.store_id + "_x", book_id, 10
            )
            assert code != 200

    def test_error_book_id(self):
        for b in self.books:
            book_id = b.id
            code = self.seller.add_stock_level(
                self.user_id, self.store_id, book_id + "_x", 10
            )
            assert code != 200

    def test_ok(self):
        for b in self.books:
            book_id = b.id
            code = self.seller.add_stock_level(self.user_id, self.store_id, book_id, 10)
            assert code == 200

```

#### 对应后端实现代码

```Python
    def add_stock_level(
        self, 
        user_id: str, 
        store_id: str, 
        book_id: str, 
        add_stock_level: int
    ):
        try:
            # 检查用户、商店和书籍是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            # 更新库存数量
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE stores
                    SET stock_level = stock_level + %s
                    WHERE store_id = %s AND book_id = %s
                """, (add_stock_level, store_id, book_id))
                self.conn.commit()
        except Exception as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
```

上述代码实现了一个商家添加书籍库存的功能，说明如下：

1. **检查用户、商店和书籍是否存在**：
   - 如果用户不存在，返回错误信息 `error.error_non_exist_user_id(user_id)`。
   - 如果商店不存在，返回错误信息 `error.error_non_exist_store_id(store_id)`。
   - 如果书籍不存在，返回错误信息 `error.error_non_exist_book_id(book_id)`。

2. **更新库存数量**：
   - 使用 SQL 语句更新 `stores` 表中的 `stock_level` 字段，将库存数量增加 `add_stock_level`。
   - 提交数据库事务。

3. **异常处理**：
   - 如果在执行过程中发生异常，捕获异常并返回错误码 `530` 和异常信息。

4. **返回结果**：
   - 如果操作成功，返回状态码 `200` 和消息 `"ok"`。


### 商家发货

#### URL
POST http://[address]/seller/ship

#### Request
Headers:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

Body:
```json
{
  "user_id": "$seller id$",
  "store_id": "$store id$",
  "order_id": "$order id$"
}
```

key | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 卖家用户ID | N
store_id | string | 商铺ID | N
order_id | string | 订单ID | N

#### Response
Status Code:
码 | 描述
--- | ---
200 | 发货成功
511 | 卖家用户ID不存在
401 | 授权失败
518 | 订单不存在
520 | 订单未支付
513 | 商店不存在
529 | 重复发货

#### 对应测试代码
```python
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
```

#### 对应后端实现代码

```Python
    def ship(
            self,
            user_id: str,
            store_id: str,
            order_id: str,
            ):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            # 检查商店是否存在
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            # 检查订单是否存在
            if not self.order_id_exist(order_id):
                return error.error_invalid_order_id(order_id)
            # 检查订单是否已经支付
            if not self.order_is_paid(order_id):
                return error.error_not_be_paid(order_id)
            # 检查订单是否已经发货
            if self.order_is_shipped(order_id):
                return error.error_order_is_shipped(order_id)
            # 更新订单状态
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE new_orders
                    SET is_shipped = TRUE
                    WHERE order_id = %s AND store_id = %s
                """, (order_id, store_id))
                self.conn.commit()
        
        except Exception as e:
            return 520, "{}".format(str(e))
        return 200, "ok"
```

上述代码实现了一个商家发货的功能，说明如下：

1. **参数检查**：
  - 检查用户是否存在，如果不存在则返回错误信息。
  - 检查商店是否存在，如果不存在则返回错误信息。
  - 检查订单是否存在，如果不存在则返回错误信息。

2. **订单状态检查**：
  - 检查订单是否已经支付，如果没有支付则返回错误信息。
  - 检查订单是否已经发货，如果已经发货则返回错误信息。

3. **更新订单状态**：
  - 如果以上所有检查都通过，则将订单的状态更新为已发货。
  - 使用 SQL 更新语句将 `new_orders` 表中对应的订单状态设置为 `TRUE`。

4. **异常处理**：
  - 如果在执行过程中发生任何异常，则捕获异常并返回错误代码和异常信息。

5. **返回结果**：
  - 如果操作成功，返回状态码 `200` 和消息 `"ok"`。


### 商家查询指定商铺订单信息


#### URL

POST http://[address]/seller/query_one_store_orders

#### Request
Headers:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

Body:
```json
{
  "user_id": "$seller id$",
  "store_id": "$store id$",
  "password": "$password$"
}
```
key | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 卖家用户ID | N
store_id | string | 商铺ID | N
password | string | 用户密码 | N

#### Response

- `Status Code`

码 | 描述
--- | :--
200 | 查询商铺订单信息成功
401 | 授权失败
511 | 用户ID不存在
513 | 商铺ID不存在
522 | 卖家不存在该商铺
530 | 其它异常

- `message`

message | 描述
--- | ---
ok  | 查询成功
authorization fail | 授权失败
non exist user id {`user_id`} | 用户不存在
non exist store id {`store_id`} | 商铺不存在
no store for user, user id {`user_id`} | 卖家不存在该商铺
Exception e | 异常信息

- `orders`


orders | 描述
--- | ---
`orders`  | 订单详情
`None` | 异常状态

#### 对应测试代码
```python
def test_query_one_store_orders_ok(self):
    # 查询商铺订单信息成功
    code, _, _ = self.seller.query_one_store_orders(self.seller.seller_id, self.store_id, self.seller_password)
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
```

#### 对应后端实现代码
```python
def query_one_store_orders(self, user_id: str, store_id: str, password) -> (int, str, list):
        try:
            # 检查用户与商店是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + ("None",)
            
            # 检查用户密码是否正确
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT password FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()
                if not user or user[0] != password:
                    return error.error_authorization_fail() + ("None",)

                # 查找用户是否存在该商店
                cursor.execute("SELECT * FROM user_store WHERE user_id = %s AND store_id = %s", (user_id, store_id))
                user_store = cursor.fetchone()
                
                if not user_store:
                    return error.error_no_store_found(user_id) + ("None",)

                # 查找该商店的所有订单
                cursor.execute("SELECT * FROM new_orders WHERE store_id = %s", (store_id,))
                orders = cursor.fetchall()

        except Exception as e:
            return 530, "{}".format(str(e)), "None"
        return 200, "ok", [dict(zip([column[0] for column in cursor.description], row)) for row in orders]

```

上述代码实现了商家查询指定商铺订单信息的功能，说明如下：

1. **检查用户与商店是否存在**：
   - 调用 `self.user_id_exist(user_id)` 方法检查用户是否存在。如果不存在，返回错误信息 `error.error_non_exist_user_id(user_id)`，并附带一个额外的 `"None"` 查询异常状态。
   - 调用 `self.store_id_exist(store_id)` 方法检查商店是否存在。如果不存在，返回错误信息 `error.error_non_exist_store_id(store_id)`，并附带一个额外的 `"None"` 查询异常状态。

2. **检查用户密码是否正确**：
   - 从数据库中查找用户信息，并检查用户提供的密码是否与数据库中的密码匹配。如果不匹配，返回错误信息 `error.error_authorization_fail()`，并附带一个额外的 `"None"` 查询异常状态。

3. **查找用户是否存在该商店**：
   - 在数据库中查找用户是否拥有指定商店。如果没有找到，返回错误信息 `error.error_no_store_found(user_id)`，并附带一个额外的 `"None"` 查询异常状态。

4. **查找该商店的所有订单**：
   - 在数据库中查找指定 `store_id` 的所有订单，并将结果转换为列表。并将订单信息返回。

5. **异常处理**：
   - 如果在执行过程中发生任何异常，捕获异常并返回状态码 `530` 和异常信息的字符串，并附带一个 `"None"` 查询异常状态。

6. **返回结果**：
  - 如果操作成功，返回状态码 `200` 和消息 `"ok"`。



### 商家查询自己的所有商铺订单信息


#### URL

POST http://[address]/seller/query_all_store_orders

#### Request
Headers:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

Body:

```json
{
  "user_id": "$seller id$",
  "password": "$password$"
}
```
key | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 卖家用户ID | N
password | string | 用户密码 | N

#### Response

- `Status Code`

码 | 描述
--- | :--
200 | 查询商铺订单信息成功
401 | 授权失败
511 | 用户ID不存在
522 | 卖家不存在商铺
530 | 其它异常

- `message`

message | 描述
--- | ---
ok  | 查询成功
authorization fail | 授权失败
non exist user id {`user_id`} | 用户不存在
no store for user, user id {`user_id`} | 卖家不存在商铺
Exception e | 异常信息

- `orders`

orders | 描述
--- | ---
`orders`  | 订单详情
`None` | 异常状态

#### 对应测试代码
```python
def test_query_all_store_orders_ok(self):
    # 查询商铺订单信息成功
    code, _, _ = self.seller.query_all_store_orders(self.seller.seller_id, self.seller_password)
    assert code == 200

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
```


#### 对应后端实现代码
```python
def query_all_store_orders(self, user_id: str, password) -> (int, str, list):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)

            # 检查用户密码是否正确
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT password FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()
                if not user or user[0] != password:
                    return error.error_authorization_fail() + ("None",)

                # 查找用户的商店
                cursor.execute("SELECT * FROM user_store WHERE user_id = %s", (user_id,))
                user_stores = cursor.fetchall()

                # 检查是否有商店
                if len(user_stores) == 0:
                    return error.error_no_store_found(user_id) + ("None",)

                all_store_orders = {}
                for user_store in user_stores:
                    store_id = user_store[1]
                    # 查找该商店的所有订单
                    cursor.execute("SELECT * FROM new_orders WHERE store_id = %s", (store_id,))
                    orders = cursor.fetchall()
                    all_store_orders[store_id] = [dict(zip([column[0] for column in cursor.description], row)) for row in orders]

        except Exception as e:
            return 530, "{}".format(str(e)), "None"
        return 200, "ok", all_store_orders
```

上述代码实现了商家查询其所有商铺订单信息的功能，说明如下：

1. **检查用户是否存在**：
   - 调用 `self.user_id_exist(user_id)` 方法检查用户是否存在。如果不存在，返回错误信息 `error.error_non_exist_user_id(user_id)`，并附带一个额外的 `"None"` 查询异常状态。

2. **检查用户密码是否正确**：
   - 从数据库中查找用户信息，并检查用户提供的密码是否与数据库中的密码匹配。如果不匹配，返回错误信息 `error.error_authorization_fail()`，并附带一个额外的 `"None"` 查询异常状态。

3. **查找用户的商店**：
   - 在数据库中查找用户拥有的所有商店。

4. **检查是否有商店**：
   - 检查用户是否拥有商店。如果没有商店，返回错误信息 `error.error_no_store_found(user_id)`，并附带一个额外的 `"None"` 查询异常状态。

5. **查找所有商店的订单**：
   - 遍历用户的每个商店，查找该商店的所有订单，并将结果存储在字典 `all_store_orders` 中，键为 `store_id`，值为订单列表。

6. **异常处理**：
   - 如果在执行过程中发生任何异常，捕获异常并返回状态码 `530` 和异常信息的字符串，并附带一个 `"None"` 查询异常状态。

7. **返回结果**：
  - 如果操作成功，返回状态码 `200` 和消息 `"ok"`。