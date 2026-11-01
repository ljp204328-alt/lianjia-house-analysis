import pymysql
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col, count, desc

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

# 先清空表，让id从1开始
conn = pymysql.connect(**MYSQL_PYTHON)
cursor = conn.cursor()
cursor.execute("TRUNCATE TABLE city_house_count_top10")
conn.commit()
conn.close()

spark = SparkSession.builder \
    .appName("CityHouseCountTop10") \
    .master("spark://hadoop:7077") \
    .config("spark.jars", "/opt/software/hive/lib/mysql-connector-java-5.1.49-bin.jar") \
    .enableHiveSupport() \
    .getOrCreate()

df = spark.table("default.dwd_lianjia_house_clean")

df = df.filter(
    (col("city").isNotNull()) & (col("city") != "")
)

city_count = df.groupBy("city") \
    .agg(count("*").alias("house_count")) \
    .orderBy(desc("house_count")) \
    .limit(10) \
    .collect()

rows = [Row(city=row["city"], house_count=row["house_count"]) for row in city_count]

result_df = spark.createDataFrame(rows)
result_df.write.format("jdbc") \
    .option("url", MYSQL_CONFIG["url"]) \
    .option("dbtable", "city_house_count_top10") \
    .option("user", MYSQL_CONFIG["user"]) \
    .option("password", MYSQL_CONFIG["password"]) \
    .option("driver", MYSQL_CONFIG["driver"]) \
    .option("characterEncoding", "utf8") \
    .option("useUnicode", "true") \
    .mode("overwrite") \
    .save()

print(f"✅ 数据已写入MySQL表: city_house_count_top10")
for item in rows:
    print(f"{item['city']}: {item['house_count']}套")

spark.stop()
