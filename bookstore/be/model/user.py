import jwt
import time
import logging
import psycopg2
from psycopg2 import sql
from be.model import error

# PostgreSQL 连接设置
class DBConn:
    def __init__(self, host="localhost", port=5432, dbname="bookstore", user="postgres", password="2792636748"):
        self.conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.cursor.close()
        self.conn.close()

# encode a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }
def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    return encoded

# decode a JWT to a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }
def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms=["HS256"])
    return decoded

class User(DBConn):
    token_lifetime: int = 3600  # 3600 seconds

    def __init__(self):
        super().__init__()

    def __check_token(self, user_id, db_token, token) -> bool:
        try:
            if db_token != token:
                return False
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]
            if ts is not None:
                now = time.time()
                if self.token_lifetime > now - ts >= 0:
                    return True
        except jwt.exceptions.InvalidSignatureError as e:  # pragma: no cover
            logging.error(str(e))
            return False

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

    def check_token(self, user_id: str, token: str) -> (int, str):
        self.cursor.execute(sql.SQL("SELECT token FROM users WHERE user_id = %s"), (user_id,))
        user_doc = self.cursor.fetchone()
        if user_doc is None:
            return error.error_authorization_fail()
        db_token = user_doc[0]
        if not self.__check_token(user_id, db_token, token):
            return error.error_authorization_fail()
        return 200, "ok"

    def check_password(self, user_id: str, password: str) -> (int, str):
        self.cursor.execute(sql.SQL("SELECT password FROM users WHERE user_id = %s"), (user_id,))
        user_doc = self.cursor.fetchone()
        if user_doc is None:
            return error.error_authorization_fail()
        
        if password != user_doc[0]:
            return error.error_authorization_fail()

        return 200, "ok"

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