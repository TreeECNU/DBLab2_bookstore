import logging
import os
import psycopg2
from psycopg2 import sql, extensions
import threading

class Store:
    database_url: str

    def __init__(self):
        self.database_url = "postgresql://postgres:2792636748@localhost:5432/bookstore"
        self.init_tables()
        self.conn = self.get_db_conn()
        self.cursor = self.conn.cursor()

    def init_tables(self):
        try:
            conn = self.get_db_conn()
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL(
                        "CREATE TABLE IF NOT EXISTS users ("
                        "user_id TEXT PRIMARY KEY, password TEXT NOT NULL, "
                        "balance INTEGER NOT NULL, token TEXT, terminal TEXT);"
                    )
                )

                cur.execute(
                    sql.SQL(
                        "CREATE TABLE IF NOT EXISTS user_store("
                        "user_id TEXT, store_id TEXT, PRIMARY KEY(user_id, store_id));"
                    )
                )

                cur.execute(
                    sql.SQL(
                        "CREATE TABLE IF NOT EXISTS stores( "
                        "store_id TEXT, book_id TEXT, book_info TEXT, stock_level INTEGER,"
                        " PRIMARY KEY(store_id, book_id))"
                    )
                )

                cur.execute(
                    sql.SQL(
                        "CREATE TABLE IF NOT EXISTS new_orders( "
                        "order_id TEXT PRIMARY KEY, user_id TEXT, store_id TEXT, is_paid TEXT, is_shipped TEXT, is_received TEXT, order_completed TEXT, status TEXT, created_time TEXT)"
                    )
                )

                cur.execute(
                    sql.SQL(
                        "CREATE TABLE IF NOT EXISTS new_order_details( "
                        "order_id TEXT, book_id TEXT, count INTEGER, price INTEGER,  "
                        "PRIMARY KEY(order_id, book_id))"
                    )
                )

            conn.commit()
        except psycopg2.Error as e:
            logging.error(e)
            conn.rollback()
        finally:
            if conn:
                conn.close()

    def get_db_conn(self) -> psycopg2.extensions.connection:
        return psycopg2.connect(self.database_url)
    
    def clear_users(self):
        try:
            self.cursor.execute(sql.SQL("DELETE FROM users"))
            self.conn.commit()
        except Exception as e:
            print(f"Error clearing users: {str(e)}")
            self.conn.rollback()
        finally:
            self.cursor.close()
            self.conn.close()


database_instance: Store = None
# global variable for database sync
init_completed_event = threading.Event()


def init_database():
    global database_instance
    database_instance = Store()


def get_db_conn():
    global database_instance
    return database_instance.get_db_conn()