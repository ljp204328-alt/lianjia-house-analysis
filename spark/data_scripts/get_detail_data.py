import pymysql
from pyspark.sql import SparkSession, Row
from pyspark.sql import functions as F
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

def safe_str(val):
    return str(val) if val is not None else "未知"

def safe_int(val):
    try:
        return int(float(val)) if val is not None else 0
    except:
        return 0

def main():
    # 先清空表，让id从1开始
    conn = pymysql.connect(**MYSQL_PYTHON)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE province_details")
    conn.commit()
    conn.close()

    spark = SparkSession.builder \
        .appName("LianJiaDetailData") \
        .master("spark://hadoop:7077") \
        .config("spark.sql.warehouse.dir", "hdfs://hadoop:9000/user/hive/warehouse") \
        .config("spark.jars", "/opt/software/hive/lib/mysql-connector-java-5.1.49-bin.jar") \
        .enableHiveSupport() \
        .getOrCreate()

    try:
        print(">>> 开始生成所有省份的详情数据...")

        # 1. 获取所有省份列表
        print(">>> 获取省份列表...")
        provinces = spark.table("default.ads_province_district_analysis_base") \
            .select("province_name").distinct().collect()

        province_names = [safe_str(row[0]) for row in provinces]
        print(f">>> 共找到 {len(province_names)} 个省份")

        MUNICIPALITIES = ['北京市', '上海市', '天津市', '重庆市']

        rows = []

        for pname in province_names:
            if not pname or pname == "province_name":
                continue

            print(f"正在处理：{pname}")
            province_data = {
                "districts": [],
                "price_distribution": [],
                "area_distribution": [],
                "rent_type_distribution": [],
                "top5_max_price": []
            }

            # 2.1 基础指标
            try:
                if pname in MUNICIPALITIES:
                    district_df = spark.table("default.dwd_lianjia_house_clean") \
                        .filter(f"city = '{pname.replace('市', '')}'") \
                        .filter(F.col("district").isNotNull() & (F.col("district") != "")) \
                        .groupBy("district") \
                        .agg(
                            F.count("*").alias("rent_count"),
                            F.avg("price").alias("avg_price"),
                            F.max("price").alias("max_price"),
                            F.avg("area").alias("avg_area")
                        ) \
                        .orderBy("rent_count", ascending=False) \
                        .collect()

                    districts = []
                    max_prices = []
                    for row in district_df:
                        item = {
                            "name": safe_str(row[0]),
                            "count": safe_int(row[1]),
                            "avg_price": safe_int(row[2]),
                            "max_price": safe_int(row[3]),
                            "avg_area": safe_int(row[4])
                        }
                        districts.append(item)
                        max_prices.append(item)

                    province_data["districts"] = districts
                    province_data["top5_max_price"] = sorted(max_prices, key=lambda x: x['max_price'], reverse=True)[:5]
                else:
                    base_df = spark.table("default.ads_province_district_analysis_base") \
                        .filter(f"province_name = '{pname}'") \
                        .select("city", "rent_count", "avg_price", "max_price", "avg_area") \
                        .orderBy("rent_count", ascending=False).limit(50).collect()

                    districts = []
                    max_prices = []
                    for row in base_df:
                        item = {
                            "name": safe_str(row[0]),
                            "count": safe_int(row[1]),
                            "avg_price": safe_int(row[2]),
                            "max_price": safe_int(row[3]),
                            "avg_area": safe_int(row[4])
                        }
                        districts.append(item)
                        max_prices.append(item)

                    province_data["districts"] = districts
                    province_data["top5_max_price"] = sorted(max_prices, key=lambda x: x['max_price'], reverse=True)[:5]
            except Exception as e:
                print(f"  - Base 表出错：{e}")

            # 2.2 价格分布
            try:
                price_df = spark.table("default.ads_province_district_analysis_price") \
                    .filter(f"province_name = '{pname}'") \
                    .select("price_range", "count") \
                    .orderBy("price_range").collect()
                province_data["price_distribution"] = [{"range": safe_str(r[0]), "count": safe_int(r[1])} for r in price_df]
            except Exception as e:
                print(f"  - Price 表出错：{e}")

            # 2.3 面积分布
            try:
                area_df = spark.table("default.ads_province_district_analysis_area") \
                    .filter(f"province_name = '{pname}'") \
                    .select("area_range", "count") \
                    .orderBy("area_range").collect()
                province_data["area_distribution"] = [{"range": safe_str(r[0]), "count": safe_int(r[1])} for r in area_df]
            except Exception as e:
                print(f"  - Area 表出错：{e}")

            # 2.4 租赁方式
            try:
                rent_df = spark.table("default.ads_province_district_analysis_rent_type") \
                    .filter(f"province_name = '{pname}'") \
                    .select("rent_type", "count") \
                    .collect()
                province_data["rent_type_distribution"] = [{"type": safe_str(r[0]), "count": safe_int(r[1])} for r in rent_df]
            except Exception as e:
                print(f"  - RentType 表出错：{e}")

            # 计算汇总数据
            total_count = sum(d.get("count", 0) for d in province_data["districts"])
            avg_price = 0
            if province_data["districts"]:
                avg_price = sum(d.get("avg_price", 0) for d in province_data["districts"]) / len(province_data["districts"])

            rows.append(Row(
                province_name=pname,
                city=province_data["districts"][0]["name"] if province_data["districts"] else "",
                rent_count=total_count,
                avg_price=round(avg_price, 2),
                max_price=province_data["top5_max_price"][0]["max_price"] if province_data["top5_max_price"] else 0,
                avg_area=province_data["districts"][0].get("avg_area", 0) if province_data["districts"] else 0,
                districts=json.dumps(province_data["districts"], ensure_ascii=False),
                price_distribution=json.dumps(province_data["price_distribution"], ensure_ascii=False),
                area_distribution=json.dumps(province_data["area_distribution"], ensure_ascii=False),
                rent_type_distribution=json.dumps(province_data["rent_type_distribution"], ensure_ascii=False),
                top5_max_price=json.dumps(province_data["top5_max_price"], ensure_ascii=False)
            ))

        # 3. 写入MySQL
        print(">>> 写入MySQL...")
        if rows:
            result_df = spark.createDataFrame(rows)
            result_df.write.format("jdbc") \
                .option("url", MYSQL_CONFIG["url"]) \
                .option("dbtable", "province_details") \
                .option("user", MYSQL_CONFIG["user"]) \
                .option("password", MYSQL_CONFIG["password"]) \
                .option("driver", MYSQL_CONFIG["driver"]) \
                .option("characterEncoding", "utf8") \
                .option("useUnicode", "true") \
                .mode("overwrite") \
                .option("truncate", "true") \
                .save()

        print(f"✅ 数据已写入MySQL表: province_details")
        print(f"📊 共处理 {len(rows)} 个省份")

    except Exception as e:
        print(f"!!! 生成失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
