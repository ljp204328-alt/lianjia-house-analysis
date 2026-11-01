"""
户型分布分析
输出：各户型类型的数量和占比（写入MySQL）
"""
import pymysql
from pyspark.sql import SparkSession, Row
import pyspark.sql.functions as F
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

# ================= 配置区域 =================
SRC_DB = "default"
SRC_TABLE = "dwd_lianjia_house_clean"

# MySQL配置
MYSQL_CONFIG = {
    "url": "jdbc:mysql://192.168.80.138:3306/lianjia_analysis?useUnicode=true&characterEncoding=utf8",
    "user": "root",
    "password": "123456",
    "driver": "com.mysql.jdbc.Driver"
}

SPARK_MASTER_URL = "spark://hadoop:7077"


def main():
    # 先清空表，让id从1开始
    conn = pymysql.connect(**MYSQL_PYTHON)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE house_type_analysis")
    conn.commit()
    conn.close()

    spark = (
        SparkSession.builder
        .appName("House_Type_Analysis")
        .master(SPARK_MASTER_URL)
        .enableHiveSupport()
        .config("spark.sql.sources.writeJobStatsTracker.enabled", "false")
        .config("spark.sql.adaptive.enabled", "false")
        .getOrCreate()
    )

    try:
        print(f"读取 DWD 表: {SRC_DB}.{SRC_TABLE}")
        df = spark.table(f"{SRC_DB}.{SRC_TABLE}")

        # 确保数据有效
        df = df.filter(
            (F.col("house_type").isNotNull()) & 
            (F.col("house_type") != "") &
            (F.col("city").isNotNull())
        )

        # 按户型分组统计
        house_type_stats = df.groupBy("house_type").agg(
            F.count("*").alias("count"),
            F.round(F.avg("price"), 2).alias("avg_price"),
            F.round(F.avg("area"), 2).alias("avg_area")
        ).orderBy(F.desc("count"))

        # 收集数据
        rows = house_type_stats.collect()
        total_count = sum(row['count'] for row in rows)

        # 构建结果
        result_list = []
        for row in rows:
            house_type = row['house_type']
            count = int(row['count'])
            percentage = round((count / total_count) * 100, 2)
            
            result_list.append({
                'house_type': house_type,
                'count': count,
                'percentage': percentage,
                'avg_price': float(row['avg_price']) if row['avg_price'] else 0,
                'avg_area': float(row['avg_area']) if row['avg_area'] else 0
            })

        # 构建最终JSON结构
        result = {
            'house_types': [item['house_type'] for item in result_list],
            'counts': [item['count'] for item in result_list],
            'percentages': [item['percentage'] for item in result_list],
            'avg_prices': [item['avg_price'] for item in result_list],
            'avg_areas': [item['avg_area'] for item in result_list],
            'total_count': total_count
        }

        # 写入MySQL
        print(">>> 写入MySQL...")
        rows = [Row(
            house_type=item['house_type'],
            count=item['count'],
            percentage=item['percentage']
        ) for item in result_list]

        result_df = spark.createDataFrame(rows)
        result_df.write.format("jdbc") \
            .option("url", MYSQL_CONFIG["url"]) \
            .option("dbtable", "house_type_analysis") \
            .option("user", MYSQL_CONFIG["user"]) \
            .option("password", MYSQL_CONFIG["password"]) \
            .option("driver", MYSQL_CONFIG["driver"]) \
            .option("characterEncoding", "utf8") \
            .option("useUnicode", "true") \
            .mode("overwrite") \
            .save()

        print(f"✓ 数据已写入MySQL表: house_type_analysis")
        print(f"✓ 共统计 {total_count} 套房源，{len(result_list)} 种户型")
        
        # 打印预览
        print("\n户型分布预览:")
        for item in result_list[:10]:
            print(f"  {item['house_type']}: {item['count']}套 ({item['percentage']}%)")

    except Exception as e:
        print(f"✗ 处理失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

