import pymysql
from pyspark.sql import SparkSession, Row
import json


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
    cursor.execute("TRUNCATE TABLE top10_buildings")
    conn.commit()
    conn.close()

    spark = SparkSession.builder \
        .appName("Top10Buildings") \
        .master("spark://hadoop:7077") \
        .config("spark.sql.warehouse.dir", "hdfs://hadoop:9000/user/hive/warehouse") \
        .enableHiveSupport() \
        .getOrCreate()

    try:
        print(">>> 开始读取数据...")
        
        # 1. 读取DWD层清洗后的数据
        df_dwd = spark.table("default.dwd_lianjia_house_clean")
        
        # 2. 过滤价格异常数据(低于500元或高于50000元的可能是异常值)
        df_valid = df_dwd.filter((df_dwd.price >= 500) & (df_dwd.price <= 50000))
        
        print(f">>> 过滤前数据量: {df_dwd.count()} 条")
        print(f">>> 过滤后数据量: {df_valid.count()} 条")
        
        # 3. 统计热门楼盘TOP10(按房源数量降序排序)
        print(">>> 计算热门楼盘TOP10...")
        top10_rows = df_valid.groupBy("community_name", "city", "district") \
            .agg({"*": "count", "price": "avg"}) \
            .withColumnRenamed("count(1)", "house_count") \
            .withColumnRenamed("avg(price)", "avg_price") \
            .orderBy("house_count", ascending=False) \
            .limit(10) \
            .collect()
        
        # 4. 组装结果 - 价格改为整数
        result = []
        for i, row in enumerate(top10_rows):
            result.append({
                "rank": i + 1,
                "community_name": safe_str(row[0]),
                "city": safe_str(row[1]),
                "district": safe_str(row[2]),
                "house_count": safe_int(row[4]),
                "avg_price": int(float(row[3])) if row[3] else 0  # ✅ 改为整数
            })
        
        # 5. 写入MySQL
        print(">>> 写入MySQL...")
        rows = [Row(
            building_name=item['community_name'],
            city=item['city'],
            district=item['district'],
            avg_price=float(item['avg_price']),
            house_count=item['house_count'],
            is_featured='否'
        ) for item in result]

        result_df = spark.createDataFrame(rows)
        result_df.write.format("jdbc") \
            .option("url", MYSQL_CONFIG["url"]) \
            .option("dbtable", "top10_buildings") \
            .option("user", MYSQL_CONFIG["user"]) \
            .option("password", MYSQL_CONFIG["password"]) \
            .option("driver", MYSQL_CONFIG["driver"]) \
            .option("characterEncoding", "utf8") \
            .option("useUnicode", "true") \
            .mode("overwrite") \
            .save()

        print("✅ 数据已成功写入MySQL表: top10_buildings")
        
    except Exception as e:
        print(f"!!! 生成失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

