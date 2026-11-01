import pymysql
from pyspark.sql import SparkSession, Row
import json
from pyspark.sql.functions import col, when


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


def safe_int(val):
    try:
        return int(float(val)) if val is not None else 0
    except:
        return 0


def safe_str(val):
    return str(val) if val is not None else "未知"


def main():
    # 先清空表，让id从1开始
    conn = pymysql.connect(**MYSQL_PYTHON)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE price_distribution")
    conn.commit()
    conn.close()

    spark = SparkSession.builder \
        .appName("PriceDistribution") \
        .master("spark://hadoop:7077") \
        .config("spark.sql.warehouse.dir", "hdfs://hadoop:9000/user/hive/warehouse") \
        .enableHiveSupport() \
        .getOrCreate()

    try:
        print(">>> 开始读取数据...")
        
        # 1. 读取DWD层清洗后的数据
        df_dwd = spark.table("default.dwd_lianjia_house_clean")
        
        # 2. 过滤合理价格范围
        df_valid = df_dwd.filter((df_dwd.price >= 500) & (df_dwd.price <= 50000))
        
        print(f">>> 过滤后数据量: {df_valid.count()} 条")
        
        # 3. 添加价格区间标签
        df_with_range = df_valid.withColumn(
            "price_range",
            when(col("price") < 1000, "0-1000")
            .when((col("price") >= 1000) & (col("price") < 2000), "1000-2000")
            .when((col("price") >= 2000) & (col("price") < 3000), "2000-3000")
            .when((col("price") >= 3000) & (col("price") < 5000), "3000-5000")
            .otherwise("5000+")
        )
        
        # 4. 按价格区间和租赁方式分组统计
        print(">>> 计算价格区间分布...")
        result_df = df_with_range.groupBy("price_range", "rent_type") \
            .agg({"*": "count"}) \
            .withColumnRenamed("count(1)", "count") \
            .orderBy("price_range")
        
        # 5. 组装结果
        zhengzu_data = {}
        hezu_data = {}
        
        for row in result_df.collect():
            price_range = row[0]
            rent_type = row[1]
            count = safe_int(row[2])
            
            if rent_type == "整租":
                zhengzu_data[price_range] = count
            elif rent_type == "合租":
                hezu_data[price_range] = count
        
        # 确保所有区间都有数据
        all_ranges = ["0-1000", "1000-2000", "2000-3000", "3000-5000", "5000+"]
        result = {
            "price_ranges": all_ranges,
            "zhengzu": [zhengzu_data.get(r, 0) for r in all_ranges],
            "hezu": [hezu_data.get(r, 0) for r in all_ranges]
        }
        
        # 6. 写入MySQL
        print(">>> 写入MySQL...")
        total_count = sum(result["zhengzu"]) + sum(result["hezu"])
        
        rows = []
        for i, price_range in enumerate(result["price_ranges"]):
            zhengzu_count = result["zhengzu"][i]
            hezu_count = result["hezu"][i]
            total = zhengzu_count + hezu_count
            
            if total > 0:
                rows.append(Row(
                    price_range=price_range,
                    count=total,
                    percentage=round((total / total_count) * 100, 2),
                    zhengzu_count=zhengzu_count,
                    hezu_count=hezu_count
                ))
        
        result_df = spark.createDataFrame(rows)
        result_df.write.format("jdbc") \
            .option("url", MYSQL_CONFIG["url"]) \
            .option("dbtable", "price_distribution") \
            .option("user", MYSQL_CONFIG["user"]) \
            .option("password", MYSQL_CONFIG["password"]) \
            .option("driver", MYSQL_CONFIG["driver"]) \
            .option("characterEncoding", "utf8") \
            .option("useUnicode", "true") \
            .mode("overwrite") \
            .save()

        print("✅ 数据已成功写入MySQL表: price_distribution")
        
    except Exception as e:
        print(f"!!! 生成失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

