from pyspark.sql import SparkSession
import os
from pathlib import Path
import pyspark.sql.functions as F

# ================= 配置区域 =================

HDFS_TARGET_PATH = os.getenv("HDFS_TARGET_PATH", "/houseData/house.csv")
HDFS_TARGET_DIR = os.getenv("HDFS_TARGET_DIR", str(Path(HDFS_TARGET_PATH).parent))
HDFS_NN_URI = os.getenv("HDFS_NN_URI", "hdfs://hadoop:9000")
TABLE_LOCATION = os.getenv(
    "HIVE_TABLE_LOCATION",
    f"{HDFS_NN_URI.rstrip('/')}/{HDFS_TARGET_DIR.lstrip('/')}",
)
METASTORE_HOST = os.getenv("METASTORE_HOST", "hadoop")
METASTORE_PORT = os.getenv("METASTORE_PORT", "9083")

DATABASE = os.getenv("HIVE_DATABASE", "default")
TABLE = os.getenv("HIVE_TABLE", "ods_lianjia_house")


def create_external_table(spark: SparkSession) -> None:
    print(f"开始加载数据: {HDFS_TARGET_PATH}")

    # 1. 创建数据库
    spark.sql(f"CREATE DATABASE IF NOT EXISTS {DATABASE}")

    # 2. 彻底删除旧表（关键步骤：清除缓存和旧数据引用）
    print(f"清理旧表 {DATABASE}.{TABLE}...")
    spark.sql(f"DROP TABLE IF EXISTS {DATABASE}.{TABLE}")
    print("✓ 旧表已清理")

    # 3. 创建新表
    ddl = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {DATABASE}.{TABLE} (
        city STRING,
        rent_type STRING,
        is_featured STRING,
        community_name STRING,
        house_type STRING,
        district STRING,
        section STRING,
        area STRING,
        direction STRING,
        tags STRING,
        price STRING,
        floor_type STRING,
        total_floors STRING,
        cover_image STRING,
        detail_url STRING
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
    WITH SERDEPROPERTIES (
        'separatorChar' = ',',
        'quoteChar' = '"',
        'escapeChar' = '\\\\'
    )
    STORED AS TEXTFILE
    LOCATION '{TABLE_LOCATION}'
    TBLPROPERTIES ('skip.header.line.count'='1')
    """
    spark.sql(ddl)
    print(f"✓ 外部表 {DATABASE}.{TABLE} 创建成功")

    # 4. 验证数据是否更新
    print("\n正在验证新数据...")
    count_df = spark.sql(f"SELECT COUNT(*) as count FROM {DATABASE}.{TABLE}")
    count_df.show()

    print("预览前 3 行数据:")
    spark.sql(f"SELECT * FROM {DATABASE}.{TABLE} LIMIT 4").show(truncate=False)


def main() -> None:
    spark = (
        SparkSession.builder
        .appName("ODS_House_Data_Load")
        .master("spark://hadoop:7077")
        .enableHiveSupport()
        .config("spark.sql.warehouse.dir", "hdfs://hadoop:9000/user/hive/warehouse")
        .getOrCreate()
    )

    try:
        create_external_table(spark)

        # 【新增】打印详细数据统计
        print("\n========== ODS 层数据统计 ==========")
        df = spark.table(f"{DATABASE}.{TABLE}")

        total_count = df.count()
        print(f"总数据量: {total_count} 条")

        # 按城市统计
        print("\n各城市数据分布:")
        df.groupBy("city").count().orderBy(F.desc("count")).show(20, truncate=False)

        # 检查空值情况
        print("\n字段空值统计:")
        for col_name in df.columns:
            null_count = df.filter(F.col(col_name).isNull() | (F.trim(F.col(col_name)) == "")).count()
            if null_count > 0:
                print(f"  {col_name}: {null_count} 条空值 ({round(null_count / total_count * 100, 2)}%)")

    except Exception as e:
        print(f"执行失败: {e}")
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
