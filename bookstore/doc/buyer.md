## 买家下单

#### URL：
POST http://[address]/buyer/new_order

#### Request

##### Header:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

##### Body:
```json
{
  "user_id": "buyer_id",
  "store_id": "store_id",
  "books": [
    {
      "id": "1000067",
      "count": 1
    },
    {
      "id": "1000134",
      "count": 4
    }
  ]
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
store_id | string | 商铺ID | N
books | class | 书籍购买列表 | N

books数组：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
id | string | 书籍的ID | N
count | string | 购买数量 | N


#### Response

Status Code:

码 | 描述
--- | ---
200 | 下单成功
5XX | 买家用户ID不存在
5XX | 商铺ID不存在
5XX | 购买的图书不存在
5XX | 商品库存不足

##### Body:
```json
{
  "order_id": "uuid"
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
order_id | string | 订单号，只有返回200时才有效 | N


## 买家付款

#### URL：
POST http://[address]/buyer/pay_to_platform

#### Request

##### Body:
```json
{
  "user_id": "buyer_id",
  "order_id": "order_id",
  "password": "password"
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单ID | N
password | string | 买家用户密码 | N 


#### Response

Status Code:

码 | 描述
--- | ---
200 | 付款成功
400 | 已付款
401 | 授权失败 
511 | 账户不存在
518 | 订单不存在
519 | 账户余额不足
526 | 订单已被取消
527 | 订单重复支付
530 | 无效参数


## 买家充值

#### URL：
POST http://[address]/buyer/add_funds

#### Request



##### Body:
```json
{
  "user_id": "user_id",
  "password": "password",
  "add_value": 10
}
```

##### 属性说明：

key | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
password | string | 用户密码 | N
add_value | int | 充值金额，以分为单位 | N


Status Code:

码 | 描述
--- | ---
200 | 充值成功
401 | 授权失败
5XX | 无效参数


## 买家确认收货
#### URL：
POST http://[address]/buyer/add_funds

#### Request



##### Body:
```json
{
  "user_id": "buyer_id",
  "order_id": "order_id",
  "password": "password"
}
```

##### 属性说明：

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单ID | N
password | string | 买家用户密码 | N 


Status Code:

码 | 描述
--- | ---
200 | 充值成功
401 | 授权失败
520 | 订单未支付
528 | 订单已收货

## 买家查询订单状态

#### URL：
POST http://[address]/buyer/query_order_status

#### Request

Headers:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

Body:

```json
{
  "user_id": "$user id$",
  "order_id": "$order id$",
  "password": "$password$"
}
```

##### 属性说明：

key | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单ID | N
password | string | 用户密码 | N

#### Response

- `Status Code`

码 | 描述
--- | ---
200 | 查询成功
401 | 授权失败
511 | 用户ID不存在
518 | 非法订单ID
530 | 其它异常


- `message`

message | 描述
--- | ---
ok  | 查询成功
authorization fail | 授权失败
non exist user id {`user_id`} | 用户ID不存在
invalid order id {`order_id`} | 非法订单ID
Exception e | 异常信息

- `order_status`


order_status | 描述
--- | ---
`pending`  | 待支付
`paid` | 已支付
`shipped` | 已发货
`received` | 已收货
`completed` | 已完成
`canceled` | 已取消
`None` | 异常状态

#### 对应测试代码
```python
def test_query_order_status_ok(self):
    # 查询成功
    code, _, _ = self.buyer.query_order_status(self.order_id, self.buyer_id, self.buyer_password)
    assert code == 200
  
def test_query_order_status_fail(self):
    # 用户ID不存在
    user_id_test = self.buyer_id + "_x"
    code, _, _ = self.buyer.query_order_status(self.order_id, user_id_test, self.buyer_password)
    assert code == 511
    # 非法订单ID
    order_id_test = self.order_id + "_x"
    code, _, _ = self.buyer.query_order_status(order_id_test, self.buyer_id, self.buyer_password)
    assert code == 518
    # 授权失败
    password_test = self.buyer_password + "_x"
    code, _, _ = self.buyer.query_order_status(self.order_id, self.buyer_id, password_test)
    assert code == 401
```

#### 对应后端实现代码
```python
def query_order_status(self, user_id: str, order_id: str, password) -> (int, str, str): # type: ignore
    try:
        # 检查用户是否存在
        if not self.user_id_exist(user_id):
            return error.error_non_exist_user_id(user_id) + ("None",)
        # 检查用户密码是否正确
        user = self.db.user.find_one({"user_id": user_id})
        if user['password'] != password:
            return error.error_authorization_fail() + ("None",)
        # 查找订单
        order = self.db.new_order.find_one({"order_id": order_id, "user_id": user_id})
        if order is None:
            return error.error_invalid_order_id(order_id) + ("None",)
        # 返回订单状态
        order_status = self.ORDER_STATUS[order['status']]
        return 200, "ok", order_status
    except Exception as e: # pragma: no cover
        return 530, "{}".format(str(e)) + ("None",)
```
上述代码实现了一个查询订单状态的功能，说明：

1. **检查用户是否存在**：
   - 调用 `self.user_id_exist(user_id)` 方法检查用户是否存在。如果不存在，返回错误信息 `error.error_non_exist_user_id(user_id)`，并附带一个额外的 `"None"` 查询异常状态。

2. **检查用户密码是否正确**：
   - 从数据库中查找用户信息，并检查用户提供的密码是否与数据库中的密码匹配。如果不匹配，返回错误信息 `error.error_authorization_fail()`，并附带一个额外的 `"None"` 查询异常状态。

3. **查找订单**：
   - 在数据库中查找指定 `order_id` 和 `user_id` 的订单。如果订单不存在，返回错误信息 `error.error_invalid_order_id(order_id)`，并附带一个额外的 `"None"` 查询异常状态。   

4. **返回订单状态**：
   - 如果订单存在，根据订单的 `status` 字段，从 `self.ORDER_STATUS` 字典中获取对应的订单状态描述，并返回状态码 `200`、消息 `"ok"` 以及订单状态描述。   
   `ORDER_STATUS` 字典定义如下:
   `
    ORDER_STATUS = {
        "pending": "待支付",
        "paid": "已支付",
        "shipped": "已发货",
        "received": "已收货",
        "completed": "已完成",
        "canceled": "已取消"
    }
   `

5. **异常处理**：
   - 如果在执行过程中发生任何异常，捕获异常并返回状态码 `530` 和异常信息的字符串，并附带一个额外的 `"None"` 查询异常状态。



## 买家查询所有订单信息

#### URL：
POST http://[address]/buyer/query_buyer_all_orders

#### Request

Headers:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

Body:

```json
{
  "user_id": "$user id$",
  "password": "$password$"
}
```

##### 属性说明：

key | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
password | string | 用户密码 | N

#### Response

- `Status Code`

码 | 描述
--- | ---
200 | 查询成功
401 | 授权失败
511 | 用户ID不存在
530 | 其它异常


- `message`

message | 描述
--- | ---
ok  | 查询成功
authorization fail | 授权失败
non exist user id {`user_id`} | 用户ID不存在
Exception e | 异常信息

- `orders`

orders | 描述
--- | ---
`orders`  | 订单详情
`None` | 异常状态

#### 对应测试代码
```python
def test_query_buyer_all_orders_ok(self):
    # 查询成功
    code, _, _ = self.buyer.query_buyer_all_orders(self.buyer_id, self.buyer_password)
    assert code == 200

def test_query_buyer_all_orders_fail(self):
    # 用户ID不存在
    user_id_test = self.buyer_id + "_x"
    code, _, _ = self.buyer.query_buyer_all_orders(user_id_test, self.buyer_password)
    assert code == 511
    # 授权失败
    password_test = self.buyer_password + "_x"
    code, _, _ = self.buyer.query_buyer_all_orders(self.buyer_id, password_test)
    assert code == 401
```

#### 对应后端实现代码

```python
def query_buyer_all_orders(self, user_id: str, password) -> (int, str, list): # type: ignore
    try:
        # 检查用户是否存在
        if not self.user_id_exist(user_id):
            return error.error_non_exist_user_id(user_id) + ("None",)
        # 检查用户密码是否正确
        user = self.db.user.find_one({"user_id": user_id})
        if user['password'] != password:
            return error.error_authorization_fail() + ("None",)
        # 查找用户的所有订单
        orders = list(self.db.new_order.find({"user_id": user_id}))
        return 200, "ok", str(orders)
    except Exception as e: # pragma: no cover
        return 530, "{}".format(str(e)), None
```

上述代码实现了一个查询买家所有订单的功能，说明如下：

1. **检查用户是否存在**：
   - 调用 `self.user_id_exist(user_id)` 方法检查用户是否存在。如果不存在，返回错误信息 `error.error_non_exist_user_id(user_id)`，并附带一个额外的 `"None"` 查询异常状态。

2. **检查用户密码是否正确**：
   - 从数据库中查找用户信息，并检查用户提供的密码是否与数据库中的密码匹配。如果不匹配，返回错误信息 `error.error_authorization_fail()`，并附带一个额外的 `"None"` 查询异常状态。

3. **查找用户的所有订单**：
   - 在数据库中查找指定 `user_id` 的所有订单，并将结果转换为列表。

4. **返回订单列表**：
   - 如果成功找到订单，返回状态码 `200`、消息 `"ok"` 以及订单列表信息。

5. **异常处理**：
   - 如果在执行过程中发生任何异常，捕获异常并返回状态码 `530` 和异常信息的字符串，并附带一个 `None`查询异常状态。




## 买家取消订单

#### URL：
POST http://[address]/buyer/cancel_order

#### Request

Headers:

key | 类型 | 描述 | 是否可为空
---|---|---|---
token | string | 登录产生的会话标识 | N

Body:
```json
{
  "user_id": "$user id$",
  "order_id": "$order id$",
  "password": "$password$"
}
```

##### 属性说明：

key | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 买家用户ID | N
order_id | string | 订单ID | N
password | string | 用户密码 | N

#### Response

- `Status Code`

码 | 描述
--- | ---
200 | 取消成功
401 | 授权失败
511 | 用户ID不存在
518 | 非法订单ID
521 | 已支付，取消订单失败
530 | 其它异常


- `message`

message | 描述
--- | ---
ok  | 取消成功
authorization fail | 授权失败
non exist user id {`user_id`} | 用户ID不存在
invalid order id {`order_id`} | 非法订单号ID
cannot be canceled, order id {`order_id`} | 已支付，取消订单失败
Exception e | 异常信息

#### 对应测试代码
```python
def test_cancel_order_ok(self):
    # 取消成功
    code, _ = self.buyer.cancel_order(self.order_id, self.buyer_id, self.buyer_password)
    assert code == 200

def test_cancel_order_fail(self):
    # 用户ID不存在
    user_id_test = self.buyer_id + "_x"
    code, _ = self.buyer.cancel_order(self.order_id, user_id_test, self.buyer_password)
    assert code == 511
    # 非法订单ID
    order_id_test = self.order_id + "_x"
    code, _ = self.buyer.cancel_order(order_id_test, self.buyer_id, self.buyer_password)
    assert code == 518
    # 授权失败
    password_test = self.buyer_password + "_x"
    code, _ = self.buyer.cancel_order(self.order_id, self.buyer_id, password_test)
    assert code == 401
    # 已支付，取消订单失败
    code = self.buyer.add_funds(self.total_price)
    assert code == 200
    code = self.buyer.payment(self.order_id)
    assert code == 200
    code, _ = self.buyer.cancel_order(self.order_id, self.buyer_id, self.buyer_password)
    assert code == 521
```

#### 对应后端实现代码

```python
def cancel_order(self, user_id: str, order_id: str, password) -> (int, str): # type: ignore
    try:
        # 检查用户是否存在
        if not self.user_id_exist(user_id):
            return error.error_non_exist_user_id(user_id)
        # 检查用户密码是否正确
        user = self.db.user.find_one({"user_id": user_id})
        if user['password'] != password:
            return error.error_authorization_fail()
        # 查找订单
        order = self.db.new_order.find_one({"order_id": order_id, "user_id": user_id})
        if order is None:
            return error.error_invalid_order_id(order_id)
        # 检查订单是否已经支付
        if order.get('is_paid', False):
            return error.error_cannot_be_canceled(order_id)
        # 取消订单，更新订单信息
        self.db.new_order.update_one(
            {"order_id": order_id},
            {"$set": {"status": "canceled"}}
        )
        # 恢复库存
        order_details = self.db.new_order_detail.find({"order_id": order_id})
        for detail in order_details:
            self.db.store.update_one(
                {"store_id": order['store_id'], "book_id": detail['book_id']},
                {"$inc": {"stock_level": detail['count']}}
            )
        # 删除订单，根据业务逻辑自选
        # self.db.new_order.delete_one({"order_id": order_id})
        # self.db.new_order_detail.delete_many({"order_id": order_id})
    except Exception as e: # pragma: no cover
        return 530, "{}".format(str(e))
    return 200, "ok"
```

上述代码实现了一个取消订单的功能，说明如下：

1. **检查用户是否存在**：
   - 调用 `self.user_id_exist(user_id)` 方法检查用户是否存在。如果不存在，返回错误信息 `error.error_non_exist_user_id(user_id)`。

2. **检查用户密码是否正确**：
   - 从数据库中查找用户信息，并检查用户提供的密码是否与数据库中的密码匹配。如果不匹配，返回错误信息 `error.error_authorization_fail()`。

3. **查找订单**：
   - 在数据库中查找指定 `order_id` 和 `user_id` 的订单。如果订单不存在，返回错误信息 `error.error_invalid_order_id(order_id)`。

4. **检查订单是否已经支付**：
   - 检查订单是否已经支付。如果订单已经支付，返回错误信息 `error.error_cannot_be_canceled(order_id)`。

5. **取消订单，更新订单信息**：
   - 更新订单的状态为 `"canceled"`。

6. **恢复库存**：
   - 查找订单的详细信息，并根据订单中的书籍数量恢复库存。

7. **删除订单（可选）**：
   - 根据业务逻辑，可以选择删除订单及其详细信息。代码中注释掉了这部分，表示这是一个可选操作。

8. **异常处理**：
   - 如果在执行过程中发生任何异常，捕获异常并返回状态码 `530` 和异常信息的字符串。



## 超时未支付，自动取消订单

#### URL：
POST http://[address]/buyer/auto_cancel_expired_orders

#### Request

定时自动发送 `request`

#### Response

- `Status Code`

码 | 描述
--- | ---
200 | 自动取消成功
530 | 其它异常


- `message`

message | 描述
--- | ---
ok  | 自动取消成功
not | 自动取消失败


#### 对应测试代码
```python
def test_auto_cancel_expired_orders(self):
    # 循环调用自动取消接口，每隔3秒一次，执行5次
    for _ in range(5):  
        code, message = self.buyer.auto_cancel_expired_orders()
        assert code == 200
        print(f"Auto cancel expired orders call result: {message}")
        time.sleep(2)  # 等待2秒
```

#### 对应后端实现代码

```python
def auto_cancel_expired_orders(self):
    try:
        # 获取当前时间
        now = datetime.utcnow()
        # 查找所有未支付的订单
        pending_orders = self.db.new_order.find({"is_paid": False})
        for order in pending_orders:
            # 确保 order 字典中存在 "created_time" 键
            if "created_time" in order:
                created_time_dict = order["created_time"]
                time_diff = abs(now - created_time_dict)
                # 超时时间为5秒，检查订单是否已经超时
                if time_diff < timedelta(seconds=5):
                    # 取消订单
                    order_id = order['order_id']
                    self.db.new_order.update_one(
                        {"order_id": order_id},
                        {"$set": {"status": "canceled"}}
                    )
                    # 恢复库存
                    order_details = self.db.new_order_detail.find({"order_id": order_id})
                    for detail in order_details:
                        self.db.store.update_one(
                            {"store_id": order['store_id'], "book_id": detail['book_id']},
                            {"$inc": {"stock_level": detail['count']}})
    except Exception as e: # pragma: no cover
        return 530, "not"
    return 200, "ok"
```

上述代码实现了一个自动取消过期订单的功能，说明如下：

1. **获取当前时间**：
   - 使用 `datetime.utcnow()` 获取当前的 UTC 时间。

2. **查找所有未支付的订单**：
   - 从数据库中查找所有 `is_paid` 为 `False` 的订单。

3. **检查订单是否超时**：
   - 遍历每个未支付的订单，检查订单的创建时间 `created_time` 是否存在。
   - 计算当前时间与订单创建时间的时间差 `time_diff`。
   - 如果时间差小于 5 秒，则认为订单未超时。

4. **取消订单并恢复库存**：
   - 如果订单超时（时间差大于等于 5 秒），则更新订单状态为 `"canceled"`。
   - 查找订单的详细信息，并根据订单中的书籍数量恢复库存。

5. **异常处理**：
   - 如果在执行过程中发生任何异常，捕获异常并返回状态码 `530` 和消息 `"not"`。
