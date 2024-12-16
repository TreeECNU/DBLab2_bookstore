import psycopg2
from psycopg2 import sql

class DBConn:
    def __init__(self):
        # 连接PostgreSQL
        self.conn = psycopg2.connect(
            dbname="bookstore",
            user="postgres",
            password="2792636748",
            host="localhost",
            port="5432"
        )
        self.conn.autocommit = True  # 自动提交事务

    def user_id_exist(self, user_id):
        # 查询users表中是否存在给定user_id
        with self.conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT 1 FROM users WHERE user_id = %s"), [user_id])
            return cur.fetchone() is not None

    def book_id_exist(self, store_id, book_id):
        # 查询stores表中是否存在对应的store_id和book_id
        with self.conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT 1 FROM stores WHERE store_id = %s AND book_id = %s"), [store_id, book_id])
            return cur.fetchone() is not None

    def store_id_exist(self, store_id):
        # 查询user_store表中是否存在给定store_id
        with self.conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT 1 FROM user_store WHERE store_id = %s"), [store_id])
            return cur.fetchone() is not None

    def order_id_exist(self, order_id):
        # 查询new_orders表中是否存在给定order_id
        with self.conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT 1 FROM new_orders WHERE order_id = %s"), [order_id])
            return cur.fetchone() is not None

    def order_is_paid(self, order_id):
        # 查询new_orders表中的order是否被支付
        with self.conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT is_paid FROM new_orders WHERE order_id = %s"), [order_id])
            result = cur.fetchone()
            return result[0] if result else False

    def order_is_shipped(self, order_id):
        # 查询new_orders表中的order是否被发货
        with self.conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT is_shipped FROM new_orders WHERE order_id = %s"), [order_id])
            result = cur.fetchone()
            return result[0] if result else False

    def close(self):
        # 关闭数据库连接
        if self.conn:
            self.conn.close()