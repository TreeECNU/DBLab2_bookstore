import os
import random
import base64
import simplejson as json
from pymongo import MongoClient
from bson.binary import Binary
import psycopg2
from typing import List

class Book:
    id: str
    title: str
    author: str
    publisher: str
    original_title: str
    translator: str
    pub_year: str
    pages: int
    price: int
    currency_unit: str
    binding: str
    isbn: str
    author_intro: str
    book_intro: str
    content: str
    tags: list
    pictures: list

    def __init__(self):
        self.tags = []
        self.pictures = []


class BookDB:
    def __init__(self, large: bool = False):
        # MongoDB 连接
        self.client = MongoClient('mongodb://localhost:27017/')  # 连接到MongoDB
        self.db = self.client['bookstore_pic']  # 数据库名称
        self.collection = self.db['books']  # 集合名称

        # PostgreSQL 连接
        self.pg_conn = psycopg2.connect(
            host='localhost',
            database='bookstore',
            user='postgres',
            password='2792636748'
        )
        self.pg_cursor = self.pg_conn.cursor() # 创建游标

    def get_book_count(self):
        # 从 PostgreSQL 获取书籍数量
        self.pg_cursor.execute("SELECT COUNT(*) FROM books;")
        count = self.pg_cursor.fetchone()[0]
        return count

    def get_book_info(self, start, size) -> List[Book]:
        books = []

        # 从 PostgreSQL 获取书籍基本信息
        self.pg_cursor.execute(
            "SELECT id, title, author, publisher, original_title, translator, "
            "pub_year, pages, price, currency_unit, binding, isbn, author_intro, "
            "book_intro, content, tags FROM books ORDER BY id LIMIT %s OFFSET %s;",
            (size, start)
        )
        rows = self.pg_cursor.fetchall()

        for row in rows:
            book = Book()
            book.id = str(row[0])
            book.title = row[1]
            book.author = row[2]
            book.publisher = row[3]
            book.original_title = row[4]
            book.translator = row[5]
            book.pub_year = row[6]
            book.pages = row[7]
            book.price = row[8]
            book.currency_unit = row[9]
            book.binding = row[10]
            book.isbn = row[11]
            book.author_intro = row[12]
            book.book_intro = row[13]
            book.content = row[14]
            book.tags = row[15]

            # 从 MongoDB 获取图片数据
            mongo_book = self.collection.find_one({'id': book.id})
            if mongo_book:
                picture_binary = mongo_book.get('picture')
                if picture_binary:
                    picture_base64 = base64.b64encode(picture_binary).decode('utf-8')
                    book.pictures.append(picture_base64)

            books.append(book)

        return books

    def __del__(self):
        # 关闭 PostgreSQL 连接
        self.pg_cursor.close()
        self.pg_conn.close()

# 写一个测试用例来测试上面的功能是否实现成功
# if __name__ == '__main__':
#     db = BookDB()
#     print(db.get_book_count())
#     print(db.get_book_info(0, 10))