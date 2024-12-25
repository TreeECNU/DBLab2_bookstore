### 注册用户

#### URL：
POST http://$address$/auth/register

#### Request

Body:
```
{
    "user_id":"$user name$",
    "password":"$user password$"
}
```

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 用户名 | N
password | string | 登陆密码 | N

#### Response

Status Code:


码 | 描述
--- | ---
200 | 注册成功
512 | 注册失败，用户名重复

Body:
```
{
    "message":"$error message$"
}
```
变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
message | string | 返回错误消息，成功时为"ok" | N

#### 对应测试代码
```Python
    def test_register_ok(self):
        code = self.auth.register(self.user_id, self.password)
        assert code == 200
    
    def test_register_error_exist_user_id(self):
        code = self.auth.register(self.user_id, self.password)
        assert code == 200

        code = self.auth.register(self.user_id, self.password)
        assert code != 200
```

#### 对应后端实现代码
```Python
    def register(self, user_id: str, password: str):
        try:
            # 检查是否已经存在相同的 user_id
            self.cursor.execute(sql.SQL("SELECT * FROM users WHERE user_id = %s"), (user_id,))
            existing_user = self.cursor.fetchone()
            if existing_user:
                return error.error_exist_user_id(user_id)

            terminal = f"terminal_{time.time()}"
            token = jwt_encode(user_id, terminal)
            self.cursor.execute(
                sql.SQL("INSERT INTO users (user_id, password, balance, token, terminal) VALUES (%s, %s, %s, %s, %s)"),
                (user_id, password, 0, token, terminal)
            )
            self.conn.commit()
        except Exception as e:  # pragma: no cover
            logging.error(f"Error during registration: {str(e)}")
            self.conn.rollback()
            return error.error_exist_user_id(user_id)
        return 200, "ok"
```

上述代码实现了一个注册用户的功能，说明如下：

1. **检查用户是否存在**：
  - 使用 SQL 查询检查数据库中是否已存在相同的 `user_id`。
  - 如果存在，返回错误信息 `error.error_exist_user_id(user_id)`。

2.  **生成终端标识和令牌**：
  - 如果用户不存在，生成一个唯一的终端标识 `terminal`，格式为 `terminal_` 加上当前时间戳。
  - 使用 JWT 编码生成一个令牌 `token`，包含 `user_id` 和 `terminal`。

3.  **插入新用户数据**：
  - 将新用户的 `user_id`、`password`、初始余额 `0`、生成的 `token` 和 `terminal` 插入到 `users` 表中。
  - 提交事务以确保数据持久化。

4.  **异常处理**：
  - 如果在注册过程中发生任何异常，记录错误日志并回滚事务，确保数据库状态一致。
  - 返回错误信息 `error.error_exist_user_id(user_id)`。

5.  **返回结果**：
  - 如果注册成功，返回状态码 `200` 和消息 `"ok"`。

### 注销用户

#### URL：
POST http://$address$/auth/unregister

#### Request

Body:
```
{
    "user_id":"$user name$",
    "password":"$user password$"
}
```

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 用户名 | N
password | string | 登陆密码 | N

#### Response

Status Code:


码 | 描述
--- | ---
200 | 注销成功
401 | 注销失败，用户名不存在或密码不正确


Body:
```
{
    "message":"$error message$"
}
```
变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
message | string | 返回错误消息，成功时为"ok" | N

#### 对应测试代码
```Python
    def test_unregister_ok(self):
        code = self.auth.register(self.user_id, self.password)
        assert code == 200

        code = self.auth.unregister(self.user_id, self.password)
        assert code == 200

    def test_unregister_error_authorization(self):
        code = self.auth.register(self.user_id, self.password)
        assert code == 200

        code = self.auth.unregister(self.user_id + "_x", self.password)
        assert code != 200

        code = self.auth.unregister(self.user_id, self.password + "_x")
        assert code != 200
```

#### 对应后端实现代码
```Python
    def unregister(self, user_id: str, password: str) -> (int, str):
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message

            self.cursor.execute(sql.SQL("DELETE FROM users WHERE user_id = %s"), (user_id,))
            self.conn.commit()
            if self.cursor.rowcount == 0:
                return error.error_authorization_fail()
        except Exception as e:  # pragma: no cover
            logging.error(f"Error during unregister: {str(e)}")
            self.conn.rollback()
            return 528, "{}".format(str(e))
        return 200, "ok"
```

上述代码实现了一个注销用户的功能，说明如下：

1. **参数校验**：
  - 接收 `user_id` 和 `password` 参数。
  - 调用 `check_password` 方法验证用户密码是否正确。如果验证失败，则直接返回错误码和消息。

2. **执行删除操作**：
  - 如果密码验证成功，执行 SQL 删除语句，从 `users` 表中删除指定 `user_id` 的用户记录。
  - 提交事务 (`self.conn.commit()`)。

3. **检查删除结果**：
  - 检查受影响的行数 (`self.cursor.rowcount`)。如果没有匹配的用户记录被删除，则调用 `error.error_authorization_fail()` 返回授权失败的错误信息。

4. **异常处理**：
  - 如果在执行过程中发生异常，捕获异常并记录错误日志 (`logging.error`)。
  - 回滚事务 (`self.conn.rollback()`) 并返回错误码 528 和异常信息。

5. **返回结果**：
  - 如果删除成功，返回状态码 200 和消息 "ok"。


### 用户登录

#### URL：
POST http://$address$/auth/login

#### Request

Body:
```
{
    "user_id":"$user name$",
    "password":"$user password$",
    "terminal":"$terminal code$"
}
```

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 用户名 | N
password | string | 登陆密码 | N
terminal | string | 终端代码 | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 登录成功
401 | 登录失败，用户名或密码错误

Body:
```
{
    "message":"$error message$",
    "token":"$access token$"
}
```
变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
message | string | 返回错误消息，成功时为"ok" | N
token | string | 访问token，用户登录后每个需要授权的请求应在headers中传入这个token | 成功时不为空

#### 说明 

1.terminal标识是哪个设备登录的，不同的设备拥有不同的ID，测试时可以随机生成。 

2.token是登录后，在客户端中缓存的令牌，在用户登录时由服务端生成，用户在接下来的访问请求时不需要密码。token会定期地失效，对于不同的设备，token是不同的。token只对特定的时期特定的设备是有效的。

#### 对应测试代码
```Python
    def test_ok(self):
        code, token = self.auth.login(self.user_id, self.password, self.terminal)
        assert code == 200

    def test_error_user_id(self):
        code, token = self.auth.login(self.user_id + "_x", self.password, self.terminal)
        assert code == 401

    def test_error_password(self):
        code, token = self.auth.login(self.user_id, self.password + "_x", self.terminal)
        assert code == 401
```

#### 对应后端实现代码
```Python
    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
        token = ""
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""

            token = jwt_encode(user_id, terminal)
            self.cursor.execute(
                sql.SQL("UPDATE users SET token = %s, terminal = %s WHERE user_id = %s"),
                (token, terminal, user_id)
            )
            self.conn.commit()
            if self.cursor.rowcount == 0:
                return error.error_authorization_fail() + ("",)
        except Exception as e:  # pragma: no cover
            logging.error(f"Error during login: {str(e)}")
            self.conn.rollback()
            return 528, "{}".format(str(e)), ""
        return 200, "ok", token
```

上述代码实现了一个用户登录的功能，说明如下：  

1. **参数校验**：
  - 接收 `user_id`、`password` 和 `terminal` 参数。
  
2.  **密码验证**：
  - 调用 `self.check_password(user_id, password)` 方法检查用户密码是否正确。
  - 如果密码验证失败（返回码不是 200），则直接返回错误信息和空字符串作为 token。

3. **生成 Token**：
  - 如果密码验证成功，使用 `jwt_encode(user_id, terminal)` 生成一个 JWT token。

4. **更新数据库**：
  - 使用生成的 token 和终端信息更新数据库中的用户记录。
  - 执行 SQL 更新语句：`UPDATE users SET token = %s, terminal = %s WHERE user_id = %s`。
  - 提交事务 (`self.conn.commit()`)。
  - 检查是否有行被更新，如果没有行被更新，则返回授权失败的错误信息。

5. **异常处理**：
  - 如果在上述过程中发生任何异常，捕获异常并记录错误日志。
  - 回滚数据库事务 (`self.conn.rollback()`)。
  - 返回错误代码 528 和异常信息。

6. **返回结果**：
  - 如果所有操作成功，返回状态码 200、消息 "ok" 和生成的 token。


### 用户更改密码

#### URL：
POST http://$address$/auth/password

#### Request

Body:
```
{
    "user_id":"$user name$",
    "oldPassword":"$old password$",
    "newPassword":"$new password$"
}
```

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 用户名 | N
oldPassword | string | 旧的登陆密码 | N
newPassword | string | 新的登陆密码 | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 更改密码成功
401 | 更改密码失败

Body:
```
{
    "message":"$error message$",
}
```
变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
message | string | 返回错误消息，成功时为"ok" | N

#### 对应测试代码
```Python
    def test_ok(self):
        code = self.auth.password(self.user_id, self.old_password, self.new_password)
        assert code == 200

        code, new_token = self.auth.login(
            self.user_id, self.old_password, self.terminal
        )
        assert code != 200

        code, new_token = self.auth.login(
            self.user_id, self.new_password, self.terminal
        )
        assert code == 200

        code = self.auth.logout(self.user_id, new_token)
        assert code == 200

    def test_error_password(self):
        code = self.auth.password(
            self.user_id, self.old_password + "_x", self.new_password
        )
        assert code != 200

        code, new_token = self.auth.login(
            self.user_id, self.new_password, self.terminal
        )
        assert code != 200

    def test_error_user_id(self):
        code = self.auth.password(
            self.user_id + "_x", self.old_password, self.new_password
        )
        assert code != 200

        code, new_token = self.auth.login(
            self.user_id, self.new_password, self.terminal
        )
        assert code != 200
```

#### 对应后端实现代码
```Python
    def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> bool:
        try:
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message

            terminal = f"terminal_{time.time()}"
            token = jwt_encode(user_id, terminal)
            self.cursor.execute(
                sql.SQL("UPDATE users SET password = %s, token = %s, terminal = %s WHERE user_id = %s"),
                (new_password, token, terminal, user_id)
            )
            self.conn.commit()
            if self.cursor.rowcount == 0:
                return error.error_authorization_fail()
        except Exception as e:  # pragma: no cover
            logging.error(f"Error during change_password: {str(e)}")
            self.conn.rollback()
            return 528, "{}".format(str(e))
        return 200, "ok"
```

上述代码实现了一个用户更改密码的功能，说明如下：

1. **验证旧密码**：
  - 调用 `self.check_password(user_id, old_password)` 检查用户提供的旧密码是否正确。
  - 如果返回的状态码不是 200（表示成功），则直接返回错误信息。

2. **生成新 token 和 terminal**：
  - 使用当前时间戳生成一个唯一的 `terminal` 标识符。
  - 使用 `jwt_encode` 函数为用户生成一个新的 JWT `token`。

3. **更新数据库**：
  - 执行 SQL 更新语句，将用户的密码、`token` 和 `terminal` 更新到数据库中。
  - 提交事务 (`self.conn.commit()`)。

4. **检查更新结果**：
  - 如果没有行被更新（即 `self.cursor.rowcount == 0`），则返回授权失败的错误信息。

5. **异常处理**：
  - 如果在执行过程中发生任何异常，记录错误日志并回滚事务 (`self.conn.rollback()`)，然后返回错误信息。

6. **返回结果**：
  - 如果一切顺利，返回状态码 200 和 "ok" 表示操作成功。

### 用户登出

#### URL：
POST http://$address$/auth/logout

#### Request

Headers:

key | 类型 | 描述
---|---|---
token | string | 访问token

Body:
```
{
    "user_id":"$user name$"
}
```

变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
user_id | string | 用户名 | N

#### Response

Status Code:

码 | 描述
--- | ---
200 | 登出成功
401 | 登出失败，用户名或token错误

Body:
```
{
    "message":"$error message$"
}
```
变量名 | 类型 | 描述 | 是否可为空
---|---|---|---
message | string | 返回错误消息，成功时为"ok" | N

#### 对应测试代码
```Python
    def test_ok(self):
        code = self.auth.logout(self.user_id + "_x", token)
        assert code == 401

        code = self.auth.logout(self.user_id, token + "_x")
        assert code == 401

        code = self.auth.logout(self.user_id, token)
        assert code == 200
```

#### 对应后端实现代码
```Python
    def logout(self, user_id: str, token: str) -> bool:
        try:
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message

            terminal = f"terminal_{time.time()}"
            dummy_token = jwt_encode(user_id, terminal)

            self.cursor.execute(
                sql.SQL("UPDATE users SET token = %s, terminal = %s WHERE user_id = %s"),
                (dummy_token, terminal, user_id)
            )
            self.conn.commit()
            if self.cursor.rowcount == 0:
                return error.error_authorization_fail()
        except Exception as e:  # pragma: no cover
            logging.error(f"Error during logout: {str(e)}")
            self.conn.rollback()
            return 528, "{}".format(str(e))
        return 200, "ok"
```

上述代码实现了一个用户登出的功能，说明如下：  

1. **验证 Token**：
  - 调用 `self.check_token(user_id, token)` 方法检查传入的 `user_id` 和 `token` 是否有效。
  - 如果验证失败（返回的状态码不是 200），直接返回错误信息。

2. **生成新的临时 Token 和终端标识**：
  - 使用当前时间戳生成一个新的终端标识 `terminal`。
  - 使用 `jwt_encode` 函数为用户生成一个无效的 `dummy_token`，用于替换数据库中的有效 Token。

3. **更新数据库**：
  - 执行 SQL 更新语句，将用户的 `token` 和 `terminal` 字段更新为新生成的无效值。
  - 提交事务 (`self.conn.commit()`)。
  - 检查是否有行受到影响（即是否找到并更新了对应的用户记录）。如果没有影响任何行，则返回授权失败的错误。

4. **异常处理**：
  - 如果在执行过程中发生异常，捕获异常并记录错误日志。
  - 回滚事务 (`self.conn.rollback()`) 并返回错误信息。

5. **返回结果**：
  - 如果所有操作都成功完成，返回状态码 200 和消息 "ok"。