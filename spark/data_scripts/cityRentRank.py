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


def safe_float(val):
    try:
        return float(val) if val is not None else 0.0
    except:
        return 0.0


# 城市到省份的映射表（与 detailADS.py 保持一致）
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
    '贵阳': '贵州省', '遵义': '贵州省', '六盘水': '贵州省', '安顺': '贵州省', '毕节': '贵州省', '铜仁': '贵州省',

    # 广西壮族自治区
    '南宁': '广西壮族自治区', '桂林': '广西壮族自治区', '柳州': '广西壮族自治区', '北海': '广西壮族自治区',
    '防城港': '广西壮族自治区',

    # 海南省
    '海口': '海南省', '三亚': '海南省', '陵水': '海南省', '澄迈': '海南省', '临高': '海南省',
    '万宁': '海南省', '儋州': '海南省',

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


def main():
    # 先清空表，让id从1开始
    conn = pymysql.connect(**MYSQL_PYTHON)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE city_rent_rank")
    conn.commit()
    conn.close()

    spark = SparkSession.builder \
        .appName("CityRentRank") \
        .master("spark://hadoop:7077") \
        .config("spark.sql.warehouse.dir", "hdfs://hadoop:9000/user/hive/warehouse") \
        .enableHiveSupport() \
        .getOrCreate()

    try:
        print(">>> 开始读取数据...")

        # 1. 读取 DWD 层清洗后的数据
        df = spark.table("default.dwd_lianjia_house_clean")

        print(f">>> 读取数据量: {df.count()} 条")

        # 2. 添加省份列
        case_expr = "CASE city " + " ".join(
            [f"WHEN '{city}' THEN '{province}'" for city, province in CITY_TO_PROVINCE.items()]
        ) + " ELSE '未知省份' END"

        df_with_province = df.withColumn("province_name", F.expr(case_expr))

        # 3. 过滤无效数据
        df_clean = df_with_province.filter(
            (F.col("province_name") != "未知省份") &
            (F.col("province_name").isNotNull()) &
            (F.col("city").isNotNull()) &
            (F.col("city") != "")
        )

        # 4. 按城市统计平均租金
        print(">>> 计算城市租金排行榜...")
        city_rent_stats = df_clean.groupBy("city", "province_name").agg(
            F.round(F.avg("price"), 2).alias("avg_price"),
            F.count("*").alias("house_count")
        )

        # 5. 按平均租金降序排序，取 TOP 20，并收集到 Python
        top20_rows = city_rent_stats.orderBy("avg_price", ascending=False).limit(20).collect()

        # 6. 在 Python 端添加排名
        result = []
        for i, row in enumerate(top20_rows):
            result.append({
                "rank": i + 1,
                "city": safe_str(row['city']),
                "province": safe_str(row['province_name']),
                "avg_price": safe_float(row['avg_price']),
                "house_count": safe_int(row['house_count'])
            })

        # 7. 显示结果
        print("\n城市租金排行榜 TOP 20:")
        for item in result:
            print(
                f"  {item['rank']}. {item['city']} | 平均租金: {item['avg_price']}元/月 | 房源数: {item['house_count']}套")

        # 8. 写入MySQL
        print(">>> 写入MySQL...")
        rows = [Row(
            city=item['city'],
            avg_price=item['avg_price'],
            house_count=item['house_count']
        ) for item in result]

        result_df = spark.createDataFrame(rows)
        result_df.write.format("jdbc") \
            .option("url", MYSQL_CONFIG["url"]) \
            .option("dbtable", "city_rent_rank") \
            .option("user", MYSQL_CONFIG["user"]) \
            .option("password", MYSQL_CONFIG["password"]) \
            .option("driver", MYSQL_CONFIG["driver"]) \
            .option("characterEncoding", "utf8") \
            .option("useUnicode", "true") \
            .mode("overwrite") \
            .save()

        print("✅ 数据已成功写入MySQL表: city_rent_rank")

    except Exception as e:
        print(f"!!! 生成失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
