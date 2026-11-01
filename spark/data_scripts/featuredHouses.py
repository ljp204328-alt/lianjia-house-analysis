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
    cursor.execute("TRUNCATE TABLE featured_houses")
    conn.commit()
    conn.close()

    spark = (
        SparkSession.builder
        .appName("Featured_Houses_Analysis")
        .master(SPARK_MASTER_URL)
        .enableHiveSupport()
        .config("spark.jars", "/opt/software/hive/lib/mysql-connector-java-5.1.49-bin.jar")
        .config("spark.sql.sources.writeJobStatsTracker.enabled", "false")
        .config("spark.sql.adaptive.enabled", "false")
        .getOrCreate()
    )

    df = spark.table(f"{SRC_DB}.{SRC_TABLE}")

    featured_houses = df.filter(df.is_featured == '是').groupBy(
        "district",
        "city",
        "rent_type",
        "house_type",
        "price",
        "community_name",
        "area",
        "direction",
        "tags",
        "cover_image",
        "detail_url"
    ).agg(
        F.count("*").alias("house_count")
    ).orderBy(
        F.desc("house_count")
    )

    result_list = featured_houses.collect()

    rows = [
        Row(
            community_name=row["community_name"] or "",
            city=row["city"] or "",
            district=row["district"] or "",
            rent_type=row["rent_type"] or "",
            house_type=row["house_type"] or "",
            area=float(row["area"]) if row["area"] else 0,
            price=float(row["price"]) if row["price"] else 0,
            direction=row["direction"] or "",
            tags=row["tags"] or "",
            cover_image=row["cover_image"] or "",
            detail_url=row["detail_url"] or "",
            house_count=int(row["house_count"]) if row["house_count"] else 0
        )
        for row in result_list
    ]

    if rows:
        result_df = spark.createDataFrame(rows)
        result_df.write.format("jdbc") \
            .option("url", MYSQL_CONFIG["url"]) \
            .option("dbtable", "featured_houses") \
            .option("user", MYSQL_CONFIG["user"]) \
            .option("password", MYSQL_CONFIG["password"]) \
            .option("driver", MYSQL_CONFIG["driver"]) \
            .option("characterEncoding", "utf8") \
            .option("useUnicode", "true") \
            .mode("overwrite") \
            .save()

    print(f"✅ 数据已写入MySQL表: featured_houses")
    print(f"📊 共处理 {len(rows)} 条必看好房数据")

    spark.stop()

if __name__ == "__main__":
    main()
