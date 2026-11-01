"""用户库（本机 zufangdata）数据访问层 —— PyMySQL 直连，兼容原 Flask 版建表结构"""
from datetime import datetime

import pymysql

from werkzeug.security import check_password_hash, generate_password_hash

from config import Config

_CREATE_USERS_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(11) NULL,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4
"""


def get_conn():
    """获取用户库连接"""
    return pymysql.connect(
        host=Config.USER_DB_HOST,
        port=Config.USER_DB_PORT,
        user=Config.USER_DB_USER,
        password=Config.USER_DB_PASSWORD,
        database=Config.USER_DB_NAME,
        charset="utf8mb4",
        connect_timeout=10,
    )


def _query(sql, params=None):
    conn = get_conn()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        conn.close()


def init_users_table():
    """确保用户表存在（幂等，兼容 Flask 版已建表结构）"""
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(_CREATE_USERS_SQL)
        conn.commit()
    finally:
        conn.close()


def find_user_by_username(username: str):
    rows = _query("SELECT * FROM users WHERE username = %s LIMIT 1", (username,))
    return rows[0] if rows else None


def find_user_by_id(user_id: int):
    rows = _query("SELECT * FROM users WHERE id = %s LIMIT 1", (user_id,))
    return rows[0] if rows else None


def create_user(username: str, password: str, phone=None):
    """创建用户并返回完整记录

    注：旧 Flask-SQLAlchemy 建表的 create_time/update_time 在 MySQL 侧无 DEFAULT
    （默认值在 ORM 的 Python 端），因此 INSERT 必须显式提供这两个列。
    """
    now = datetime.now()
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash, phone, "
                "create_time, update_time) VALUES (%s, %s, %s, %s, %s)",
                (username, generate_password_hash(password), phone, now, now),
            )
            conn.commit()
            new_id = cursor.lastrowid
    finally:
        conn.close()
    return find_user_by_id(new_id)


def verify_password(user_row: dict, raw_password: str) -> bool:
    return check_password_hash(user_row["password_hash"], raw_password)
