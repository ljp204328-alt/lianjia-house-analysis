import pymysql
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col, count, round as spark_round

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
cursor.execute("TRUNCATE TABLE rent_type_analysis")
conn.commit()
conn.close()

spark = SparkSession.builder \
    .appName("RentTypeAnalysis") \
    .master("spark://hadoop:7077") \
    .config("spark.jars", "/opt/software/hive/lib/mysql-connector-java-5.1.49-bin.jar") \
    .enableHiveSupport() \
    .getOrCreate()

df = spark.table("default.dwd_lianjia_house_clean")

df = df.filter(
    (col("rent_type").isNotNull()) & (col("rent_type") != "")
)

total_count = df.count()

rent_type_dist = df.groupBy("rent_type") \
    .agg(count("*").alias("count")) \
    .orderBy(col("count").desc()) \
    .collect()

rows = []
for row in rent_type_dist:
    rows.append(Row(
        rent_type=row["rent_type"],
        count=row["count"],
        percentage=round(row["count"] / total_count * 100, 1)
    ))

result_df = spark.createDataFrame(rows)
result_df.write.format("jdbc") \
    .option("url", MYSQL_CONFIG["url"]) \
    .option("dbtable", "rent_type_analysis") \
    .option("user", MYSQL_CONFIG["user"]) \
    .option("password", MYSQL_CONFIG["password"]) \
    .option("driver", MYSQL_CONFIG["driver"]) \
    .option("characterEncoding", "utf8") \
    .option("useUnicode", "true") \
    .mode("overwrite") \
    .save()

print(f"✅ 数据已写入MySQL表: rent_type_analysis，总计: {total_count}套")

spark.stop()
