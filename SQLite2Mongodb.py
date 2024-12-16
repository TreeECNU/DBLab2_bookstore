import sqlite3
from pymongo import MongoClient
from bson.binary import Binary

# 连接到SQLite数据库
sqlite_conn = sqlite3.connect('bookstore/fe/data/book.db')
sqlite_cursor = sqlite_conn.cursor()

# 连接到MongoDB数据库
mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_db = mongo_client['bookstore_pic']  # 替换为你的数据库名称
mongo_collection = mongo_db['books']

# 从SQLite中查询book表的所有记录
sqlite_cursor.execute("SELECT * FROM book")
rows = sqlite_cursor.fetchall()

# 遍历每一行并插入到MongoDB中
for row in rows:
    book_data = {
        'id': row[0],
        'picture': Binary(row[16])  # 将BLOB数据转为Binary
    }
    
    # 插入到MongoDB中
    mongo_collection.insert_one(book_data)

# 关闭数据库连接
sqlite_conn.close()
mongo_client.close()

print("数据迁移完成！")
