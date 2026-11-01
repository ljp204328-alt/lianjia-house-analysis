from pyspark.sql import SparkSession
import pyspark.sql.functions as F

# ================= 配置区域 =================
SRC_DB = "default"
SRC_TABLE = "dwd_lianjia_house_clean"

DST_DB = "default"
DST_TABLE = "ads_province_district_analysis"

# HDFS 基础路径
HDFS_BASE_PATH = "/user/hive/warehouse/ads_province_data"

METASTORE_URI = "thrift://hadoop:9083"
SPARK_MASTER_URL = "spark://hadoop:7077"

# 城市到省份的映射表（基于 DWD 实际数据）
CITY_TO_PROVINCE = {
    # 四川省
    '成都': '四川省', '绵阳': '四川省', '德阳': '四川省', '达州': '四川省', '巴中': '四川省', '凉山': '四川省',
        '宜宾': '四川省', '乐山': '四川省', '南充': '四川省', '攀枝花': '四川省', '广元': '四川省', '遂宁': '四川省',
        '资阳': '四川省', '雅安': '四川省',

    # 重庆市
    '重庆': '重庆市',

    # 陕西省
    '西安': '陕西省', '咸阳': '陕西省', '宝鸡': '陕西省', '汉中': '陕西省',

    # 甘肃省
    '兰州': '甘肃省', '天水': '甘肃省',

    # 青海省
    '西宁': '青海省',

    # 宁夏回族自治区
    '银川': '宁夏回族自治区',

    # 新疆维吾尔自治区
    '乌鲁木齐': '新疆维吾尔自治区',

    # 西藏自治区
    '拉萨': '西藏自治区',

    # 云南省
    '昆明': '云南省', '大理': '云南省', '西双版纳': '云南省',

    # 贵州省
    '贵阳': '贵州省',

    # 广西壮族自治区
    '南宁': '广西壮族自治区', '桂林': '广西壮族自治区', '柳州': '广西壮族自治区', '北海': '广西壮族自治区',
    '防城港': '广西壮族自治区',

    # 海南省
    '海口': '海南省', '三亚': '海南省', '陵水': '海南省', '澄迈': '海南省', '临高': '海南省', '万宁': '海南省',

    # 广东省
    '广州': '广东省', '深圳': '广东省', '东莞': '广东省', '佛山': '广东省', '珠海': '广东省', '中山': '广东省',
    '惠州': '广东省', '江门': '广东省', '湛江': '广东省', '清远': '广东省',

    # 湖南省
    '长沙': '湖南省', '株洲': '湖南省', '湘潭': '湖南省', '衡阳': '湖南省', '岳阳': '湖南省', '常德': '湖南省',
    '湘西': '湖南省',

    # 湖北省
    '武汉': '湖北省', '宜昌': '湖北省', '襄阳': '湖北省', '黄冈': '湖北省', '黄石': '湖北省', '鄂州': '湖北省',

    # 河南省
    '郑州': '河南省', '洛阳': '河南省', '开封': '河南省', '新乡': '河南省', '许昌': '河南省', '平顶山': '河南省',
    '周口': '河南省', '驻马店': '河南省', '濮阳': '河南省', '三门峡': '河南省', '济源': '河南省',

    # 山东省
    '济南': '山东省', '青岛': '山东省', '烟台': '山东省', '潍坊': '山东省', '威海': '山东省', '临沂': '山东省',
    '济宁': '山东省', '淄博': '山东省', '泰安': '山东省', '菏泽': '山东省',

    # 江苏省
    '南京': '江苏省', '苏州': '江苏省', '无锡': '江苏省', '常州': '江苏省', '南通': '江苏省', '徐州': '江苏省',
    '扬州': '江苏省', '盐城': '江苏省', '镇江': '江苏省', '淮安': '江苏省', '昆山': '江苏省', '常熟': '江苏省',
    '太仓': '江苏省', '丹阳': '江苏省', '江阴': '江苏省', '句容': '江苏省', '海门': '江苏省',

    # 浙江省
    '杭州': '浙江省', '宁波': '浙江省', '温州': '浙江省', '嘉兴': '浙江省', '绍兴': '浙江省', '金华': '浙江省',
    '湖州': '浙江省', '台州': '浙江省', '衢州': '浙江省', '义乌': '浙江省',

    # 安徽省
    '合肥': '安徽省', '芜湖': '安徽省', '蚌埠': '安徽省', '安庆': '安徽省', '阜阳': '安徽省', '滁州': '安徽省',
    '六安': '安徽省', '马鞍山': '安徽省',

    # 江西省
    '南昌': '江西省', '九江': '江西省', '赣州': '江西省', '吉安': '江西省', '上饶': '江西省',

    # 福建省
    '福州': '福建省', '厦门': '福建省', '泉州': '福建省', '漳州': '福建省',

    # 上海市
    '上海': '上海市',

    # 北京市
    '北京': '北京市',

    # 天津市
    '天津': '天津市',

    # 河北省
    '石家庄': '河北省', '唐山': '河北省', '保定': '河北省', '廊坊': '河北省', '秦皇岛': '河北省', '邯郸': '河北省',
    '张家口': '河北省', '承德': '河北省', '涿州': '河北省',

    # 山西省
    '太原': '山西省', '大同': '山西省', '临汾': '山西省',

    # 内蒙古自治区
    '呼和浩特': '内蒙古自治区', '包头': '内蒙古自治区', '赤峰': '内蒙古自治区', '通辽': '内蒙古自治区',
    '巴彦淖尔': '内蒙古自治区',

    # 辽宁省
    '沈阳': '辽宁省', '大连': '辽宁省', '丹东': '辽宁省', '抚顺': '辽宁省',

    # 吉林省
    '长春': '吉林省', '吉林': '吉林省',

    # 黑龙江省
    '哈尔滨': '黑龙江省', '大庆': '黑龙江省'
}


def write_to_external_table(spark, df, table_name, hdfs_sub_path):
    """辅助函数：使用 CSV 写入 + 外部表映射，确保 MapReduce 能读取"""
    full_path = f"{HDFS_BASE_PATH}/{hdfs_sub_path}"

    # 1. 删除旧表（元数据）
    spark.sql(f"DROP TABLE IF EXISTS {DST_DB}.{table_name}")

    # 2. 直接写 CSV 文件到 HDFS
    print(f"正在写入 CSV: {full_path}")
    df.coalesce(1).write.mode("overwrite").format("csv").option("header", "true").save(full_path)

    # 3. 创建外部表指向该路径 (使用 OpenCSVSerde)
    schema_fields = [f"`{col}` {dtype}" for col, dtype in df.dtypes]
    schema_str = ", ".join(schema_fields)

    spark.sql(f"""
        CREATE EXTERNAL TABLE {DST_DB}.{table_name} ({schema_str})
        ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
        WITH SERDEPROPERTIES (
            'separatorChar' = ',',
            'quoteChar' = '"',
            'escapeChar' = '\\\\'
        )
        STORED AS TEXTFILE
        LOCATION '{full_path}'
        TBLPROPERTIES ('skip.header.line.count'='1')
    """)
    print(f"✓ 外部表 {table_name} 已创建")


def main():
    spark = (
        SparkSession.builder
        .appName("ADS_Province_District_Analysis")
        .master(SPARK_MASTER_URL)
        .enableHiveSupport()
        .config("spark.sql.sources.writeJobStatsTracker.enabled", "false")
        .config("spark.sql.adaptive.enabled", "false")
        .getOrCreate()
    )

    try:
        spark.sql(f"CREATE DATABASE IF NOT EXISTS {DST_DB}")

        # 1. 读取 DWD 层数据
        print(f"读取 DWD 表: {SRC_DB}.{SRC_TABLE}")
        df = spark.table(f"{SRC_DB}.{SRC_TABLE}")

        # 2. 添加省份列
        case_expr = "CASE city " + " ".join(
            [f"WHEN '{city}' THEN '{province}'" for city, province in CITY_TO_PROVINCE.items()]
        ) + " ELSE '未知省份' END"

        df_with_province = df.withColumn("province_name", F.expr(case_expr))

        # 3. 过滤 NULL 值
        df_clean = df_with_province.filter(
            (F.col("province_name") != "未知省份") &
            (F.col("province_name").isNotNull()) &
            (F.col("city").isNotNull()) &
            (F.col("city") != "")
        )

        # 确保数值类型
        df_clean = df_clean.withColumn("price", F.col("price").cast("double"))
        df_clean = df_clean.withColumn("area", F.col("area").cast("double"))

        # ================= 聚合指标 =================

        # 1. 各城市基础指标
        district_stats = df_clean.groupBy("province_name", "city").agg(
            F.count("*").alias("rent_count"),
            F.round(F.avg("price"), 2).alias("avg_price"),
            F.round(F.max("price"), 2).alias("max_price"),
            F.round(F.avg("area"), 2).alias("avg_area")
        )

        # 2. 价格区间分布
        price_dist = df_clean.withColumn(
            "price_range",
            F.when(F.col("price") < 1000, "0-1000")
            .when((F.col("price") >= 1000) & (F.col("price") < 2000), "1000-2000")
            .when((F.col("price") >= 2000) & (F.col("price") < 3000), "2000-3000")
            .otherwise("3000+")
        ).groupBy("province_name", "city", "price_range") \
            .agg(F.count("*").alias("count"))

        # 3. 面积区间分布
        area_dist = df_clean.withColumn(
            "area_range",
            F.when(F.col("area") < 50, "0-50")
            .when((F.col("area") >= 50) & (F.col("area") < 80), "50-80")
            .when((F.col("area") >= 80) & (F.col("area") < 120), "80-120")
            .otherwise("120+")
        ).groupBy("province_name", "city", "area_range") \
            .agg(F.count("*").alias("count"))

        # 4. 租赁方式分布
        rent_type_dist = df_clean.groupBy("province_name", "city", "rent_type") \
            .agg(F.count("*").alias("count"))

        # ================= 写入 ADS 表 =================
        print(f"\n写入 ADS 表: {DST_DB}.{DST_TABLE}")

        # 调用 CSV 写入函数
        write_to_external_table(spark, district_stats, f"{DST_TABLE}_base", "base_data")
        write_to_external_table(spark, price_dist, f"{DST_TABLE}_price", "price_data")
        write_to_external_table(spark, area_dist, f"{DST_TABLE}_area", "area_data")
        write_to_external_table(spark, rent_type_dist, f"{DST_TABLE}_rent_type", "rent_type_data")

        print("✓ ADS 层数据已生成")

        # ================= 详细统计 =================
        print(f"\n========== ADS 层数据统计 ==========")

        # 1. 基础指标统计
        print(f"\n【基础指标】各省份城市数量:")
        base_df = spark.sql(
            f"SELECT province_name, COUNT(DISTINCT city) as city_count, SUM(rent_count) as total_rent FROM {DST_DB}.{DST_TABLE}_base GROUP BY province_name ORDER BY total_rent DESC")
        base_df.show(30, truncate=False)

        print(f"\n【基础指标】Top 10 城市租金排名:")
        top10_df = spark.sql(
            f"SELECT province_name, city, rent_count, avg_price, max_price FROM {DST_DB}.{DST_TABLE}_base ORDER BY rent_count DESC LIMIT 10")
        top10_df.show(truncate=False)

        # 2. 价格区间统计
        print(f"\n【价格区间】整体分布:")
        price_total = spark.sql(
            f"SELECT price_range, SUM(count) as total FROM {DST_DB}.{DST_TABLE}_price GROUP BY price_range ORDER BY price_range")
        price_total.show(truncate=False)

        print(f"\n【价格区间】各省份Top价格区间:")
        price_province = spark.sql(
            f"SELECT province_name, price_range, count FROM {DST_DB}.{DST_TABLE}_price WHERE count IN (SELECT MAX(count) FROM {DST_DB}.{DST_TABLE}_price t2 WHERE t2.province_name = {DST_TABLE}_price.province_name GROUP BY province_name) ORDER BY province_name")
        price_province.show(30, truncate=False)

        # 3. 面积区间统计
        print(f"\n【面积区间】整体分布:")
        area_total = spark.sql(
            f"SELECT area_range, SUM(count) as total FROM {DST_DB}.{DST_TABLE}_area GROUP BY area_range ORDER BY area_range")
        area_total.show(truncate=False)

        # 4. 租赁方式统计
        print(f"\n【租赁方式】整体分布:")
        rent_total = spark.sql(
            f"SELECT rent_type, SUM(count) as total FROM {DST_DB}.{DST_TABLE}_rent_type GROUP BY rent_type ORDER BY total DESC")
        rent_total.show(truncate=False)

        print(f"\n【租赁方式】各省份分布:")
        rent_province = spark.sql(
            f"SELECT province_name, rent_type, count FROM {DST_DB}.{DST_TABLE}_rent_type ORDER BY province_name, count DESC")
        rent_province.show(30, truncate=False)

        # 5. 数据汇总
        print(f"\n========== 数据汇总 ==========")
        total_cities = spark.sql(f"SELECT COUNT(DISTINCT city) FROM {DST_DB}.{DST_TABLE}_base").collect()[0][0]
        total_provinces = \
        spark.sql(f"SELECT COUNT(DISTINCT province_name) FROM {DST_DB}.{DST_TABLE}_base").collect()[0][0]
        total_rents = spark.sql(f"SELECT SUM(rent_count) FROM {DST_DB}.{DST_TABLE}_base").collect()[0][0]
        avg_price = spark.sql(f"SELECT ROUND(AVG(avg_price), 2) FROM {DST_DB}.{DST_TABLE}_base").collect()[0][0]

        print(f"覆盖省份数: {total_provinces}")
        print(f"覆盖城市数: {total_cities}")
        print(f"总房源数: {total_rents}")
        print(f"平均租金: {avg_price} 元/月")

    except Exception as e:
        print(f"✗ ADS 处理失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
