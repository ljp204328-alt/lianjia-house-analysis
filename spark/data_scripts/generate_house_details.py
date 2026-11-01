#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成房屋详情数据 - 写入MySQL
"""

import pymysql
from pyspark.sql import SparkSession, Row

# pymysql配置
MYSQL_PYTHON = {
    "host": "192.168.80.138",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "lianjia_analysis",
    "charset": "utf8mb4"
}

# MySQL配置
MYSQL_CONFIG = {
    "url": "jdbc:mysql://192.168.80.138:3306/lianjia_analysis?useUnicode=true&characterEncoding=utf8",
    "user": "root",
    "password": "123456",
    "driver": "com.mysql.jdbc.Driver"
}

def main():
    # 先清空表，让id从1开始
    conn = pymysql.connect(**MYSQL_PYTHON)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE house_details")
    conn.commit()
    conn.close()

    print(">>> 生成房屋详情数据...")
    spark = SparkSession.builder \
        .appName("HouseDetails") \
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
                house_type,
                rent_type,
                area,
                price,
                direction,
                floor_type,
                total_floors,
                tags,
                cover_image,
                detail_url
            FROM dwd_lianjia_house_clean
            WHERE community_name IS NOT NULL 
            AND community_name != ''
            AND price > 0
        """)
        
        rows_data = df.collect()
        rows = [Row(
            city=row.city or "",
            district=row.district or "",
            community_name=row.community_name or "",
            house_type=row.house_type or "",
            area=float(row.area) if row.area else 0,
            price=float(row.price) if row.price else 0,
            direction=row.direction or "",
            floor_type=row.floor_type or "",
            total_floors=int(row.total_floors) if row.total_floors else 0,
            tags=row.tags or "",
            cover_image=row.cover_image or "",
            detail_url=row.detail_url or ""
        ) for row in rows_data]
        
        if rows:
            result_df = spark.createDataFrame(rows)
            result_df.write.format("jdbc") \
                .option("url", MYSQL_CONFIG["url"]) \
                .option("dbtable", "house_details") \
                .option("user", MYSQL_CONFIG["user"]) \
                .option("password", MYSQL_CONFIG["password"]) \
                .option("driver", MYSQL_CONFIG["driver"]) \
                .option("characterEncoding", "utf8") \
                .option("useUnicode", "true") \
                .mode("overwrite") \
                .save()
            
        print(f"✅ 数据已写入MySQL表: house_details，共 {len(rows)} 条")
    finally:
        spark.stop()

if __name__ == '__main__':
    main()
