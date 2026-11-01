import pymysql

from config import Config


def get_connection():
    """获取业务库（lianjia_analysis）连接"""
    return pymysql.connect(**Config.MYSQL_CONFIG)


def execute_query(sql, params=None):
    """执行查询并返回结果（字典列表）"""
    conn = get_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        conn.close()
