import pymysql
from pyspark.sql import SparkSession, Row
import pyspark.sql.functions as F

SRC_DB = "default"
SRC_TABLE = "dwd_lianjia_house_clean"
SPARK_MASTER_URL = "spark://hadoop:7077"

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
    cursor.execute("TRUNCATE TABLE city_rent_trend")
    conn.commit()
    conn.close()

    spark = (
        SparkSession.builder
        .appName("City_Rent_Trend_Analysis")
        .master(SPARK_MASTER_URL)
        .enableHiveSupport()
        .config("spark.jars", "/opt/software/hive/lib/mysql-connector-java-5.1.49-bin.jar")
        .config("spark.sql.sources.writeJobStatsTracker.enabled", "false")
        .config("spark.sql.adaptive.enabled", "false")
        .getOrCreate()
    )

    df = spark.table(f"{SRC_DB}.{SRC_TABLE}")

    df = df.filter(
        (F.col("rent_type").isNotNull()) & (F.trim(F.col("rent_type")) != "") &
        (F.col("city").isNotNull()) & (F.trim(F.col("city")) != "") &
        (F.col("price").isNotNull()) & (F.col("price") > 0)
    )

    rent_trend = df.groupBy("city", "rent_type").agg(
        F.round(F.avg("price"), 0).alias("avg_price"),
        F.count("*").alias("house_count")
    ).orderBy("city")

    result_list = rent_trend.collect()

    rows = []
    for row in result_list:
        city = row["city"]
        rent_type = row["rent_type"]
        avg_price = float(row["avg_price"]) if row["avg_price"] is not None else 0

        rows.append(Row(
            city=city,
            avg_price=avg_price,
            trend_type=rent_type
        ))

    if rows:
        result_df = spark.createDataFrame(rows)
        result_df.write.format("jdbc") \
            .option("url", MYSQL_CONFIG["url"]) \
            .option("dbtable", "city_rent_trend") \
            .option("user", MYSQL_CONFIG["user"]) \
            .option("password", MYSQL_CONFIG["password"]) \
            .option("driver", MYSQL_CONFIG["driver"]) \
            .option("characterEncoding", "utf8") \
            .option("useUnicode", "true") \
            .mode("overwrite") \
            .save()

    print(f"✅ 数据已写入MySQL表: city_rent_trend")
    print(f"📊 共处理 {len(rows)} 条数据")

    spark.stop()

if __name__ == "__main__":
    main()
