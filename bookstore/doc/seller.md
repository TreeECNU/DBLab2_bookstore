## 创建商铺



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
5XX | 商铺ID已存在


## 商家添加书籍信息

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
5XX | 卖家用户ID不存在
5XX | 商铺ID不存在
5XX | 图书ID已存在


## 商家添加书籍库存


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
5XX | 商铺ID不存在 
5XX | 图书ID不存在 
## 商家发货

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

## 商家查询指定商铺订单信息


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
def query_one_store_orders(self, user_id: str, store_id: str, password) -> (int, str, list): # type: ignore
    try:
        # 检查用户与商店是否存在
        if not self.user_id_exist(user_id):
            return error.error_non_exist_user_id(user_id) + ("None",)
        if not self.store_id_exist(store_id):
            return error.error_non_exist_store_id(store_id) + ("None",)
        # 检查用户密码是否正确
        user = self.db.user.find_one({"user_id": user_id})
        if user['password'] != password:
            return error.error_authorization_fail() + ("None",)
        # 查找用户是否存在该商店
        user_store = self.db.user_store.find_one({"user_id": user_id, "store_id": store_id})
        if not user_store:
            return error.error_no_store_found(user_id) + ("None",)
        # 查找该商店的所有订单
        orders = list(self.db.new_order.find({"store_id": store_id}))
    except Exception as e: # pragma: no cover
        return 530, "{}".format(str(e)), "None"
    return 200, "ok", str(orders)
```

上述代码实现了卖家查询指定商铺订单信息的功能，说明如下：

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



## 商家查询自己的所有商铺订单信息


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
def query_all_store_orders(self, user_id: str, password) -> (int, str, list): # type: ignore
    try:
        # 检查用户是否存在
        if not self.user_id_exist(user_id):
            return error.error_non_exist_user_id(user_id) + ("None",)
        # 检查用户密码是否正确
        user = self.db.user.find_one({"user_id": user_id})
        if user['password'] != password:
            return error.error_authorization_fail() + ("None",)
        # 查找用户的商店
        user_stores = self.db.user_store.find({"user_id": user_id})
        # 检查是否有商店
        if self.db.user_store.count_documents({"user_id": user_id}) == 0:
            return error.error_no_store_found(user_id) + ("None",)
        all_store_orders = {}
        for user_store in user_stores:
            store_id = user_store['store_id']
            # 查找该商店的所有订单
            orders = list(self.db.new_order.find({"store_id": store_id}))
            all_store_orders[store_id] = orders
    except Exception as e: # pragma: no cover
        return 530, "{}".format(str(e)), "None"
    return 200, "ok", str(all_store_orders)
```

上述代码实现了卖家查询其所有商铺订单信息的功能，说明如下：

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
