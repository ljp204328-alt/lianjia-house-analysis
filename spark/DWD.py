import os
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

# ================= 配置区域 =================
SRC_DB = "default"
SRC_TABLE = "ods_lianjia_house"

DST_DB = "default"
DST_TABLE = "dwd_lianjia_house_clean"

# HDFS 存储路径
HDFS_DATA_PATH = "/user/hive/warehouse/dwd_lianjia_house_clean_data"

SPARK_MASTER_URL = "spark://hadoop:7077"
METASTORE_URI = "thrift://hadoop:9083"

# 允许为空的字段（仅这两个可以为空）
NULLABLE_FIELDS = ["direction", "tags"]

# 不允许为空的必填字段
REQUIRED_FIELDS = [
    "city", "rent_type", "is_featured", "community_name",
    "house_type", "district", "section", "area",
    "price", "floor_type", "total_floors",
    "cover_image", "detail_url"
]


def main():
    spark = (
        SparkSession.builder
        .appName("DWD_Clean_Data")
        .master(SPARK_MASTER_URL)
        .enableHiveSupport()
        .config("spark.sql.sources.writeJobStatsTracker.enabled", "false")
        .config("spark.sql.adaptive.enabled", "false")
        .getOrCreate()
    )

    try:
        print(f"正在读取: {SRC_DB}.{SRC_TABLE}")
        df = spark.table(f"{SRC_DB}.{SRC_TABLE}")

        original_count = df.count()
        print(f"\n========== ODS 原始数据统计 ==========")
        print(f"原始数据量: {original_count} 条")

        print("\n原始数据各城市分布:")
        df.groupBy("city").count().orderBy(F.desc("count")).show(20, truncate=False)

        print("\n========== 原始数据字段空值统计 ==========")
        for col_name in df.columns:
            null_count = df.filter(
                F.col(col_name).isNull() | (F.trim(F.col(col_name)) == "")
            ).count()
            if null_count > 0:
                print(f"  {col_name}: {null_count} 条空值 ({round(null_count / original_count * 100, 2)}%)")

        print("\n开始清洗数据...")

        # ====== 第一步：过滤所有必填字段的空值（direction 和 tags 除外）======
        filter_condition = None
        for field in REQUIRED_FIELDS:
            cond = F.col(field).isNotNull() & (F.trim(F.col(field)) != "")
            if filter_condition is None:
                filter_condition = cond
            else:
                filter_condition = filter_condition & cond

        before_required_filter = df.count()
        df = df.filter(filter_condition)
        after_required_filter = df.count()
        print(f"\n【过滤1】必填字段不为空: {before_required_filter} → {after_required_filter} (删除 {before_required_filter - after_required_filter} 条)")

        # ====== 第二步：字段类型转换 ======
        df_clean = (
            df.withColumn("area", F.regexp_replace("area", "㎡", "").cast("double"))
            .withColumn("price", F.regexp_replace("price", "/月", "").cast("double"))
            .withColumn("total_floors", F.regexp_replace("total_floors", "层", "").cast("int"))
        )

        # ====== 第三步：过滤类型转换后产生的空值（非数字格式导致的cast失败）======
        before_cast_filter = df_clean.count()
        df_clean = df_clean.filter(
            F.col("area").isNotNull() &
            F.col("price").isNotNull() &
            F.col("total_floors").isNotNull()
        )
        after_cast_filter = df_clean.count()
        print(f"【过滤2】类型转换有效: {before_cast_filter} → {after_cast_filter} (删除 {before_cast_filter - after_cast_filter} 条)")

        # ====== 第四步：过滤价格异常数据 ======
        before_price_valid = df_clean.count()
        df_clean = df_clean.filter((F.col("price") > 0) & (F.col("area") > 0))
        after_price_valid = df_clean.count()
        print(f"【过滤3】price>0 且 area>0: {before_price_valid} → {after_price_valid} (删除 {before_price_valid - after_price_valid} 条)")

        # ====== 第五步：按detail_url去重 ======
        before_dedup = df_clean.count()
        df_clean = df_clean.dropDuplicates(["detail_url"])
        after_dedup = df_clean.count()
        print(f"【去重】按URL去重: {before_dedup} → {after_dedup} (删除重复 {before_dedup - after_dedup} 条)")

        final_count = df_clean.count()

        # ====== 第六步：清洗后空值验证 ======
        print(f"\n========== 清洗后字段空值验证 ==========")
        has_null = False
        for col_name in df_clean.columns:
            if col_name in NULLABLE_FIELDS:
                continue
            null_count = df_clean.filter(
                F.col(col_name).isNull() | (F.trim(F.col(col_name).cast("string")) == "")
            ).count()
            if null_count > 0:
                print(f"  ⚠ {col_name}: 仍有 {null_count} 条空值")
                has_null = True
        if not has_null:
            print("  ✓ 所有必填字段均无空值")

        # ====== 第七步：写入 HDFS ======
        print(f"\n正在写入 HDFS: {HDFS_DATA_PATH}")

        try:
            spark.sql(f"DROP TABLE IF EXISTS {DST_DB}.{DST_TABLE}")
        except:
            pass

        df_clean.coalesce(1).write.mode("overwrite").format("parquet").save(HDFS_DATA_PATH)

        print(f"正在创建外部表: {DST_DB}.{DST_TABLE}")
        spark.sql(f"""
                CREATE EXTERNAL TABLE IF NOT EXISTS {DST_DB}.{DST_TABLE} (
                    city STRING, rent_type STRING, is_featured STRING, community_name STRING,
                    house_type STRING, district STRING, section STRING, area DOUBLE,
                    direction STRING, tags STRING, price DOUBLE, floor_type STRING,
                    total_floors INT, cover_image STRING, detail_url STRING
                ) STORED AS PARQUET
                LOCATION '{HDFS_DATA_PATH}'
            """)

        print("✓ DWD 层数据生成成功！")

        # ====== 第八步：验证统计 ======
        print(f"\n========== DWD 层数据统计 ==========")
        print(f"原始数据: {original_count} 条")
        print(f"清洗后数据: {final_count} 条")
        print(f"总删除: {original_count - final_count} 条")
        print(f"保留率: {round(final_count / original_count * 100, 2)}%")

        print(f"\n清洗后各城市数据分布:")
        df_clean.groupBy("city").count().orderBy(F.desc("count")).show(20, truncate=False)

        print(f"\n预览前 3 行数据:")
        spark.sql(f"SELECT * FROM {DST_DB}.{DST_TABLE} LIMIT 3").show(truncate=False)

    except Exception as e:
        print(f" DWD 处理失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
