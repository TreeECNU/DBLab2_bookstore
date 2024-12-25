### 买家下单

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
513 | 商铺ID不存在
515 | 购买的图书不存在
519 | 商品库存不足

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

#### 对应测试代码
```Python
    def test_non_exist_book_id(self):
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=True, low_stock_level=False
        )
        assert ok
        code, _ = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code != 200

    def test_low_stock_level(self):
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=True
        )
        assert ok
        code, _ = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code != 200

    def test_ok(self):
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False
        )
        assert ok
        code, _ = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200

    def test_non_exist_user_id(self):
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False
        )
        assert ok
        self.buyer.user_id = self.buyer.user_id + "_x"
        code, _ = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code != 200

    def test_non_exist_store_id(self):
        ok, buy_book_id_list = self.gen_book.gen(
            non_exist_book_id=False, low_stock_level=False
        )
        assert ok
        code, _ = self.buyer.new_order(self.store_id + "_x", buy_book_id_list)
        assert code != 200
```

#### 对应后端实现代码
```Python
    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)
            
            # 生成订单ID
            uid = f"{user_id}_{store_id}_{uuid.uuid1()}"

            # 遍历每本书籍及其数量
            for book_id, count in id_and_count:
                # 查找书籍库存
                with self.conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT stock_level, book_info 
                        FROM stores 
                        WHERE store_id = %s AND book_id = %s
                    """, (store_id, book_id))
                    store_item = cursor.fetchone()

                if store_item is None:
                    return error.error_non_exist_book_id(book_id) + (order_id,)
                
                stock_level, book_info_str = store_item
                book_info = json.loads(book_info_str)
                price = book_info.get("price")

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)
                
                # 更新库存
                with self.conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE stores 
                        SET stock_level = stock_level - %s 
                        WHERE store_id = %s AND book_id = %s AND stock_level >= %s
                    """, (count, store_id, book_id, count))
                    if cursor.rowcount == 0:
                        return error.error_stock_level_low(book_id) + (order_id,)
                
                # 插入订单详情
                with self.conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO new_order_details (order_id, book_id, count, price) 
                        VALUES (%s, %s, %s, %s)
                    """, (uid, book_id, count, price))
            
            # 插入订单，新增 is_shipped 和 is_received 初始为 False
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO new_orders (order_id, store_id, user_id, is_paid, is_shipped, is_received, order_completed, status, created_time) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (uid, store_id, user_id, False, False, False, False, "pending", datetime.utcnow()))
            
            self.conn.commit()
            order_id = uid
        except Exception as e:
            logging.error(f"Error creating new order: {e}")
            self.conn.rollback()
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id
```

上述代码实现了一个买家下单的功能，说明如下：  

1. **参数校验**：
  - 检查用户ID是否存在，如果不存在返回错误。
  - 检查商店ID是否存在，如果不存在返回错误。

2.  **生成订单ID**：
  - 使用用户ID、商店ID和UUID生成唯一的订单ID。

3. **遍历书籍列表**：
  - 对于每本书籍及其数量：
    - 查询书籍在指定商店中的库存信息。
    - 如果书籍不存在，返回错误。
    - 获取书籍的价格。
    - 检查库存是否足够，如果不足返回错误。
    - 更新库存，减少相应数量。
    - 插入订单详情到数据库。

4. **插入订单信息**：
  - 将订单信息插入到订单表中，设置初始状态（如未支付、未发货、未收货等）。
  
5. **提交事务**：
  - 提交所有数据库操作。
  - 设置 `order_id` 为生成的唯一ID。

6. **异常处理**：
  - 如果过程中出现任何异常，记录错误日志并回滚事务，返回错误信息。

7. **返回结果**：
  - 返回状态码、消息和订单ID。


### 买家付款

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

#### 对应测试代码
```Python
    def test_ok(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200

    def test_authorization_error(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        self.buyer.password = self.buyer.password + "_x"
        code = self.buyer.payment(self.order_id)
        assert code == 401

    def test_not_suff_funds(self):
        code = self.buyer.add_funds(self.total_price - 1)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 519

    def test_repeat_pay(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200

        code = self.buyer.payment(self.order_id)
        assert code == 527

    def test_order_is_exist(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        
        self.order_id = self.order_id + "_x"

        code = self.buyer.payment(self.order_id)
        assert code == 518

    def test_pay_order_id_is_equal(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        
        self.buyer.user_id = self.buyer.user_id + "_x"
        
        code = self.buyer.payment(self.order_id)
        assert code == 401

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
```

#### 对应后端实现代码
```Python
    def pay_to_platform(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            # 查找订单
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM new_orders WHERE order_id = %s", (order_id,))
                order = cursor.fetchone()

            if order is None:
                return error.error_invalid_order_id(order_id)

            buyer_id = order[1]

            # 检查用户身份
            if buyer_id != user_id:
                return error.error_authorization_fail()

            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (buyer_id,))
                user = cursor.fetchone()

            if user is None or user[1] != password:
                return error.error_authorization_fail()
                

            # 检查是否已经付款
            if order[3]:
                return error.error_order_is_paid(order_id)

            # 计算订单总价
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT count, price FROM new_order_details WHERE order_id = %s", (order_id,))
                order_details = cursor.fetchall()

            total_price = sum(count * price for count, price in order_details)

            if user[2] < total_price:
                return error.error_not_sufficient_funds(order_id)

            # 扣除买家的余额，平台收款
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET balance = balance - %s 
                    WHERE user_id = %s AND balance >= %s
                """, (total_price, buyer_id, total_price))
                if cursor.rowcount == 0:
                    return error.error_not_sufficient_funds(order_id)

            # 更新订单状态为已付款
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE new_orders 
                    SET is_paid = %s 
                    WHERE order_id = %s
                """, (True, order_id))

            self.conn.commit()

        except Exception as e:
            logging.error(f"Error paying to platform: {e}")
            self.conn.rollback()
            return 530, "{}".format(str(e))

        return 200, "ok"
```

上述代码实现了一个买家付款的功能，说明如下：

1. **查找订单**：根据提供的 `order_id` 查找对应的订单信息。
    - 如果找不到订单，返回无效订单ID错误。

2. **检查用户身份**：
    - 确认订单中的买家ID与传入的 `user_id` 是否一致。
    - 验证用户的密码是否正确。
    - 如果任意一项不匹配，返回授权失败错误。

3. **检查订单状态**：
    - 如果订单已经被支付过，返回订单已支付错误。

4. **计算订单总价**：
    - 查询订单详情表以获取每个商品的数量和单价，计算总金额。

5. **检查余额**：
    - 检查用户的余额是否足够支付订单总价。
    - 如果余额不足，返回资金不足错误。

6. **更新用户余额和订单状态**：
    - 扣除用户账户中的余额。
    - 更新订单状态为已付款。
    - 提交事务到数据库。

7. **异常处理**：
    - 如果在执行过程中发生任何异常，记录日志并回滚事务，返回相应的错误信息。

8. **返回结果**：
    - 函数返回成功状态码和确认消息。

### 买家充值

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

#### 对应测试代码
```Python
    def test_ok(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200

    def test_authorization_error(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        self.buyer.password = self.buyer.password + "_x"
        code = self.buyer.payment(self.order_id)
        assert code == 401

    def test_not_suff_funds(self):
        code = self.buyer.add_funds(self.total_price - 1)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 519

    def test_repeat_pay(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200

        code = self.buyer.payment(self.order_id)
        assert code == 527

    def test_order_is_exist(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        
        self.order_id = self.order_id + "_x"

        code = self.buyer.payment(self.order_id)
        assert code == 518

    def test_pay_order_id_is_equal(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        
        self.buyer.user_id = self.buyer.user_id + "_x"
        
        code = self.buyer.payment(self.order_id)
        assert code == 401

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
```

#### 对应后端实现代码
```Python
    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()

            if user is None or user[1] != password:
                return error.error_authorization_fail()

            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users
                    SET balance = balance + %s 
                    WHERE user_id = %s
                """, (add_value, user_id))

            self.conn.commit()

        except Exception as e:
            logging.error(f"Error adding funds: {e}")
            self.conn.rollback()
            return 530, "{}".format(str(e))

        return 200, "ok"
```

上述代码实现了一个买家充值的功能，说明如下：
  
1. **用户验证**：
  - 使用 `user_id` 查询数据库中的用户信息。
  - 如果用户不存在或提供的密码不匹配，则返回授权失败的错误信息。

2. **更新余额**：
  - 如果用户验证通过，执行SQL语句更新用户的余额，将当前余额加上 `add_value`。

3. **提交事务**：
  - 更新成功后，提交事务以确保更改保存到数据库中。

4. **异常处理**：
  - 如果在操作过程中发生任何异常，记录错误日志，回滚事务以保证数据一致性，并返回包含错误信息的状态码530。

5. **返回结果**：
  - 操作成功则返回状态码200和确认消息"ok"。


### 买家确认收货
#### URL：
POST http://[address]/buyer/confirm_receipt_and_pay_to_seller

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

#### 对应测试代码
```Python
    def test_confirm_receipt(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        
        code = self.buyer.payment(self.order_id)
        assert code == 200

        code = self.buyer.confirm_receipt_and_pay_to_seller(self.order_id)
        assert code == 200

    def test_authorization_error(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200

        self.buyer.password = self.buyer.password + "_x"
        code = self.buyer.confirm_receipt_and_pay_to_seller(self.order_id)
        assert code == 401
    
    def test_buyer_user_id_is_equal(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200

        code = self.buyer.payment(self.order_id)
        assert code == 200

        self.buyer.user_id = self.buyer.user_id + "_x"

        code = self.buyer.confirm_receipt_and_pay_to_seller(self.order_id)
        assert code == 401

    def test_repeat_confirm_receipt(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200

        code = self.buyer.payment(self.order_id)
        assert code == 200

        code = self.buyer.confirm_receipt_and_pay_to_seller(self.order_id)
        assert code == 200

        code = self.buyer.confirm_receipt_and_pay_to_seller(self.order_id)
        assert code == 528

    def test_not_paid(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200

        code = self.buyer.confirm_receipt_and_pay_to_seller(self.order_id)
        assert code == 520
```

#### 对应后端实现代码
```Python
    def confirm_receipt_and_pay_to_seller(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            # 查找订单
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM new_orders WHERE order_id = %s", (order_id,))
                order = cursor.fetchone()

            buyer_id = order[1]

            # 检查用户身份
            if buyer_id != user_id:
                return error.error_authorization_fail()
            
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (buyer_id,))
                user = cursor.fetchone()

            if user is None or user[1] != password:
                return error.error_authorization_fail()
            
            # 检查是否已经付款
            if not order[3]:
                return error.error_not_be_paid(order_id)

            # 检查是否已确认收货
            if order[5]:
                return error.error_order_is_confirmed(order_id)

            buyer_id = order[1]
            store_id = order[2]

            with self.conn.cursor() as cursor:
                cursor.execute("SELECT user_id FROM user_store WHERE store_id = %s", (store_id,))
                seller = cursor.fetchone()
                seller_id = seller[0]

            # 计算订单总价
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT count, price FROM new_order_details WHERE order_id = %s", (order_id,))
                order_details = cursor.fetchall()

            total_price = sum(count * price for count, price in order_details)

            # 平台将钱转给卖家
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET balance = balance + %s 
                    WHERE user_id = %s
                """, (total_price, seller_id))

            # 更新订单状态为已确认收货
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE new_orders 
                    SET is_received = %s 
                    WHERE order_id = %s
                """, (True, order_id))

            # 更新订单状态为已完成
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE new_orders 
                    SET order_completed = %s 
                    WHERE order_id = %s
                """, (True, order_id))

            self.conn.commit()

        except Exception as e:
            logging.error(f"Error confirming receipt and paying to seller: {e}")
            self.conn.rollback()
            return 530, "{}".format(str(e))

        return 200, "ok"
```

上述代码实现了一个买家确认收获的功能，说明如下：

1. **查找订单**：根据提供的 `order_id` 从数据库中获取订单信息。
2. **检查用户身份**：
  - 确认订单的买家ID是否与传入的 `user_id` 匹配。
  - 验证用户的密码是否正确。如果任意一项验证失败，则返回授权失败错误。
3. **检查订单状态**：
  - 检查订单是否已经付款，如果没有则返回未付款错误。
  - 检查订单是否已经被确认收货，如果是则返回订单已确认错误。
4. **获取卖家信息**：通过订单中的 `store_id` 获取对应的卖家ID。
5. **计算订单总价**：从 `new_order_details` 表中获取订单详情并计算总价。
6. **转账给卖家**：将订单总价加到卖家账户余额中。
7. **更新订单状态**：
  - 将订单状态更新为已确认收货。
  - 将订单状态更新为已完成。
8. **提交事务**：所有操作成功后提交数据库事务。
9. **异常处理**：如果过程中发生任何异常，记录错误日志，并回滚数据库事务，返回错误信息。
10. **返回结果**：
  - 操作成功则返回状态码200和确认消息"ok"。


### 买家查询订单状态

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
def query_order_status(self, user_id: str, order_id: str, password) -> (int, str, str):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)
            
            # 检查用户密码是否正确
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()

            if user is None or user[1] != password:
                return error.error_authorization_fail() + ("None",)

            # 查找订单
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM new_orders WHERE order_id = %s AND user_id = %s", (order_id, user_id))
                order = cursor.fetchone()

            if order is None:
                return error.error_invalid_order_id(order_id) + ("None",)

            # 返回订单状态
            order_status = self.ORDER_STATUS[order[7]]

            return 200, "ok", order_status
        except Exception as e:
            logging.error(f"Error querying order status: {e}")
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

6. **返回结果**：
  - 操作成功则返回状态码200和确认消息"ok"。



### 买家查询所有订单信息

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
def query_buyer_all_orders(self, user_id: str, password) -> (int, str, list):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)
            
            # 检查用户密码是否正确
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()

            if user is None or user[1] != password:
                return error.error_authorization_fail() + ("None",)

            # 查找用户的所有订单
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM new_orders WHERE user_id = %s", (user_id,))
                orders = cursor.fetchall()

            # 将查询结果转换为字典列表
            orders_list = [dict(zip([column[0] for column in cursor.description], row)) for row in orders]

            return 200, "ok", orders_list
        except Exception as e:
            logging.error(f"Error querying buyer all orders: {e}")
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

6. **返回结果**：
  - 操作成功则返回状态码200和确认消息"ok"。


### 买家取消订单

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
def cancel_order(self, user_id: str, order_id: str, password) -> (int, str):
        try:
            # 检查用户是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)

            # 检查用户密码是否正确
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()

            if user is None or user[1] != password:
                return error.error_authorization_fail()

            # 查找订单
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM new_orders WHERE order_id = %s AND user_id = %s", (order_id, user_id))
                order = cursor.fetchone()

            if order is None:
                return error.error_invalid_order_id(order_id)

            # 检查订单是否已经支付
            if order[3]:
                return error.error_cannot_be_canceled(order_id)

            # 取消订单，更新订单信息
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE new_orders 
                    SET status = %s 
                    WHERE order_id = %s
                """, ("canceled", order_id))

            # 恢复库存
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT book_id, count FROM new_order_details WHERE order_id = %s", (order_id,))
                order_details = cursor.fetchall()

            for book_id, count in order_details:
                with self.conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE stores 
                        SET stock_level = stock_level + %s 
                        WHERE store_id = %s AND book_id = %s
                    """, (count, order[1], book_id))

            self.conn.commit()

        except Exception as e:
            logging.error(f"Error canceling order: {e}")
            self.conn.rollback()
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

7. **异常处理**：
   - 如果在执行过程中发生任何异常，捕获异常并返回状态码 `530` 和异常信息的字符串。

8. **返回结果**：
  - 操作成功则返回状态码200和确认消息"ok"。



### 超时未支付，自动取消订单

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
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM new_orders WHERE is_paid = %s", (False,))
                pending_orders = cursor.fetchall()

            for order in pending_orders:
                created_time_str = order["created_time"]
                created_time = datetime.strptime(created_time_str, "%Y-%m-%d %H:%M:%S.%f")

                if created_time is not None:
                    time_diff = abs(now - created_time)

                    # 超时时间为5秒，检查订单是否已经超时
                    if time_diff > timedelta(seconds=5):
                        # 取消订单
                        order_id = order["order_id"]
                        with self.conn.cursor() as cursor:
                            cursor.execute("""
                                UPDATE new_orders 
                                SET status = %s 
                                WHERE order_id = %s
                            """, ("canceled", order_id))
                        
                        # 恢复库存
                        with self.conn.cursor() as cursor:
                            cursor.execute("SELECT book_id, count FROM new_order_details WHERE order_id = %s", (order_id,))
                            order_details = cursor.fetchall()

                        for book_id, count in order_details:
                            with self.conn.cursor() as cursor:
                                cursor.execute("""
                                    UPDATE stores 
                                    SET stock_level = stock_level + %s 
                                    WHERE store_id = %s AND book_id = %s
                                """, (count, order["store_id"], book_id))

            self.conn.commit()
        
        except Exception as e:
            logging.error(f"Error auto-canceling expired orders: {e}")
            self.conn.rollback()
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

6. **返回结果**：
  - 操作成功则返回状态码200和确认消息"ok"。

### 查询库存

#### URL：
POST http://[address]/buyer/check_stock_level

#### Request

定时自动发送 `request`

#### Response

- `Status Code`

码 | 描述
--- | ---
200 | 查询成功
530 | 其它异常


- `message`

message | 描述
--- | ---
ok  | 查询成功
not | 查询失败


#### 对应测试代码
```python
    # 检查库存是否正确
        code, now_stock_level, _ = self.order_api.check_stock_level(self.store_id, self.book_id)
        expected_stock_level = self.stock_level - num_orders * id_and_count[0][1]
        assert code == 200
        assert now_stock_level == expected_stock_level
```

#### 对应后端实现代码

```Python
    def check_stock_level(self, store_id: str, book_id: str):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT stock_level FROM stores WHERE store_id = %s AND book_id = %s", (store_id, book_id))
                stock_level = cursor.fetchone()[0]
            return 200, stock_level, "ok"
        except Exception as e:
            logging.error(f"Error checking stock level: {e}")
            self.conn.rollback()
            return 530, -1, "{}".format(str(e))
```

上述代码实现了一个查询库存的功能，说明如下：

1. **执行查询**：
  - 执行SQL查询，从 `stores` 表中获取指定 `store_id` 和 `book_id` 的库存水平 (`stock_level`)。

2. **异常处理**：
  - 如果查询过程中发生异常，记录错误日志并回滚数据库事务。
  - 返回状态码 `530`、默认库存水平 `-1` 和异常信息。  
3. **返回结果**：
  - 如果查询成功，返回状态码 `200`、库存水平 `stock_level` 和消息 `"ok"`。

### 查询订单数量

#### URL：
POST http://[address]/buyer/check_order_count

#### Request

定时自动发送 `request`

#### Response

- `Status Code`

码 | 描述
--- | ---
200 | 查询成功
530 | 其它异常


- `message`

message | 描述
--- | ---
ok  | 查询成功
not | 查询失败


#### 对应测试代码
```python
    # 检查订单数量是否正确
        code, order_count, _ = self.order_api.check_order_count(self.user_id)
        assert code == 200
        assert order_count == num_orders
```

#### 对应后端实现代码

```Python
    def check_order_count(self, user_id: str):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM new_orders WHERE user_id = %s", (user_id,))
                order_count = cursor.fetchone()[0]
                return 200, order_count, "ok"
        except Exception as e:
            logging.error(f"Error checking order count: {e}")
            self.conn.rollback()
            return 530, -1, "{}".format(str(e))
```

上述代码实现了一个查询订单数量的功能，说明如下：

1. **执行查询**：
  - 执行SQL查询，从 `new_orders` 表中获取指定 `user_id` 的订单数量 (`order_count`)。

2. **异常处理**：
  - 如果查询过程中发生异常，记录错误日志并回滚数据库事务。
  - 返回状态码 `530`、默认库存水平 `-1` 和异常信息。  
3. **返回结果**：
  - 如果查询成功，返回状态码 `200`、库存水平 `stock_level` 和消息 `"ok"`。