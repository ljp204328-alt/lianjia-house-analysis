#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成小区/楼盘统计数据 - 写入MySQL community_stats表
"""

from pyspark.sql import SparkSession, Row
import pymysql

# pymysql配置
MYSQL_PYTHON = {
    "host": "192.168.80.138",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "lianjia_analysis",
    "charset": "utf8mb4"
}

# Spark JDBC配置
MYSQL_SPARK = {
    "url": "jdbc:mysql://192.168.80.138:3306/lianjia_analysis?useUnicode=true&characterEncoding=utf8",
    "user": "root",
    "password": "123456",
    "driver": "com.mysql.jdbc.Driver"
}

def main():
    print(">>> 启动 Spark 生成小区统计数据...")
    
    # 先清空表，让id从1开始
    conn = pymysql.connect(**MYSQL_PYTHON)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE community_stats")
    conn.commit()
    conn.close()
    
    spark = SparkSession.builder \
        .appName("CommunityStats") \
        .master("spark://hadoop:7077") \
        .config("spark.jars", "/opt/software/hive/lib/mysql-connector-java-5.1.49-bin.jar") \
        .enableHiveSupport() \
        .getOrCreate()
    try:
        df = spark.sql("""
            SELECT 
                city,
                district,
                community_name,
                COUNT(*) as count,
                ROUND(AVG(price), 2) as avg_price
            FROM dwd_lianjia_house_clean
            WHERE community_name IS NOT NULL 
            AND community_name != ''
            AND price > 0
            GROUP BY city, district, community_name
            ORDER BY city, district, count DESC
        """)
        
        rows_data = df.collect()
        rows = [Row(
            city=row.city,
            district=row.district,
            community_name=row.community_name,
            count=int(row['count']),
            avg_price=float(row['avg_price'])
        ) for row in rows_data]
        
        if rows:
            result_df = spark.createDataFrame(rows)
            result_df.write.format("jdbc") \
                .option("url", MYSQL_SPARK["url"]) \
                .option("dbtable", "community_stats") \
                .option("user", MYSQL_SPARK["user"]) \
                .option("password", MYSQL_SPARK["password"]) \
                .option("driver", MYSQL_SPARK["driver"]) \
                .mode("overwrite") \
                .save()
            
        print(f"✅ 数据已写入MySQL表: community_stats，共 {len(rows)} 条")
    finally:
        spark.stop()

if __name__ == '__main__':
    main()
