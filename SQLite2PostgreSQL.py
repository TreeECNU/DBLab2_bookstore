import sqlite3
import psycopg2
from psycopg2 import sql

# 连接到SQLite数据库
sqlite_conn = sqlite3.connect('bookstore/fe/data/book.db')
sqlite_cursor = sqlite_conn.cursor()

# 连接到PostgreSQL数据库
postgres_conn = psycopg2.connect(
    dbname='bookstore',
    user='postgres',
    password='2792636748',
    host='localhost',
    port='5432'
)
postgres_cursor = postgres_conn.cursor()

# 创建表（如果不存在）
postgres_cursor.execute("""
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title TEXT,
    author TEXT,
    publisher TEXT,
    original_title TEXT,
    translator TEXT,
    pub_year TEXT,
    pages INTEGER,
    price REAL,
    currency_unit TEXT,
    binding TEXT,
    isbn TEXT,
    author_intro TEXT,
    book_intro TEXT,
    content TEXT,
    tags TEXT
);
""")
postgres_conn.commit()

# 定义要读取的列（不包括 picture 列）
columns_to_read = [
    'id', 'title', 'author', 'publisher', 'original_title', 'translator',
    'pub_year', 'pages', 'price', 'currency_unit', 'binding', 'isbn',
    'author_intro', 'book_intro', 'content', 'tags'
]

# 构建查询语句，只选择需要的列
columns_str = ', '.join(columns_to_read)
sqlite_cursor.execute(f"SELECT {columns_str} FROM book")
rows = sqlite_cursor.fetchall()

# 遍历每一行并插入到PostgreSQL中
insert_query = sql.SQL("""
INSERT INTO books ({})
VALUES ({})
""").format(
    sql.SQL(', ').join(map(sql.Identifier, columns_to_read)),  # 插入的列名
    sql.SQL(', ').join(sql.Placeholder() * len(columns_to_read))  # 占位符
)

for row in rows:
    try:
        # 插入到PostgreSQL中
        postgres_cursor.execute(insert_query, row)
    except Exception as e:
        print(f"Failed to insert row {row} due to error: {e}")
        postgres_conn.rollback()
        continue
    else:
        postgres_conn.commit()

# 关闭数据库连接
sqlite_conn.close()
postgres_conn.close()

print("数据迁移完成！")