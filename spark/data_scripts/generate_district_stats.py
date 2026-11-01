#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成区县统计数据 - 写入MySQL
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
    cursor.execute("TRUNCATE TABLE district_price_count")
    conn.commit()
    conn.close()

    print(">>> 启动 Spark 生成区县统计数据...")
    print("=" * 50)

    spark = SparkSession.builder \
        .appName("GenerateDistrictStats") \
        .master("spark://hadoop:7077") \
        .config("spark.jars", "/opt/software/hive/lib/mysql-connector-java-5.1.49-bin.jar") \
        .enableHiveSupport() \
        .getOrCreate()

    try:
        df = spark.sql("""
            SELECT 
                city,
                district,
                COUNT(*) as house_count,
                ROUND(AVG(price), 2) as avg_price
            FROM dwd_lianjia_house_clean
            WHERE city IS NOT NULL 
            AND city != ''
            AND district IS NOT NULL 
            AND district != ''
            AND price IS NOT NULL
            AND price > 0
            GROUP BY city, district
            ORDER BY city, house_count DESC
        """)

        rows_data = df.collect()

        rows = [Row(
            city=row["city"],
            district=row["district"],
            count=int(row["house_count"]),
            avg_price=float(row["avg_price"])
        ) for row in rows_data]

        if rows:
            result_df = spark.createDataFrame(rows)
            result_df.write.format("jdbc") \
                .option("url", MYSQL_CONFIG["url"]) \
                .option("dbtable", "district_price_count") \
                .option("user", MYSQL_CONFIG["user"]) \
                .option("password", MYSQL_CONFIG["password"]) \
                .option("driver", MYSQL_CONFIG["driver"]) \
                .option("characterEncoding", "utf8") \
                .option("useUnicode", "true") \
                .mode("overwrite") \
                .save()

        print(f"✅ 数据已写入MySQL表: district_price_count，共 {len(rows)} 条")
        print("=" * 50)

    except Exception as e:
        print(f"❌ 生成失败: {e}")
    finally:
        spark.stop()


if __name__ == '__main__':
    main()
