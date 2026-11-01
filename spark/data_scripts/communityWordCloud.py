import pymysql
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col, count, avg
import jieba
import re
from collections import Counter

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
cursor.execute("TRUNCATE TABLE community_wordcloud")
conn.commit()
conn.close()

spark = SparkSession.builder \
    .appName("CommunityWordCloud") \
    .master("spark://hadoop:7077") \
    .config("spark.jars", "/opt/software/hive/lib/mysql-connector-java-5.1.49-bin.jar") \
    .enableHiveSupport() \
    .getOrCreate()

df = spark.table("default.dwd_lianjia_house_clean")

community_df = df.select("community_name") \
    .filter(col("community_name").isNotNull()) \
    .filter(col("community_name") != "") \
    .filter(col("community_name") != "未知")

community_names = [row["community_name"] for row in community_df.collect()]

print(f"总共收集到 {len(community_names)} 个楼盘名称")

stop_words = set([
    '小区', '花园', '家园', '苑', '城', '村', '公寓', '大厦', '广场', '中心',
    '一期', '二期', '三期', '四期', '五期',
    '区', '栋', '号楼', '单元',
    '的', '之', '与', '和', '在', '是', '了', '有', '都', '就', '不', '也', '这', '那'
])

all_words = []
for name in community_names:
    clean_name = re.sub(r'[0-9\d\s]+', '', name)
    words = jieba.cut(clean_name)
    filtered_words = [w for w in words if w not in stop_words and len(w) > 1]
    all_words.extend(filtered_words)

word_counts = Counter(all_words)
top_words = word_counts.most_common(100)

print(f"\n前20个高频词:")
for word, count_val in top_words[:20]:
    print(f"{word}: {count_val}")

# 写入MySQL
rows = [Row(community_name=word, count=count_val) for word, count_val in top_words]

if rows:
    result_df = spark.createDataFrame(rows)
    result_df.write.format("jdbc") \
        .option("url", MYSQL_CONFIG["url"]) \
        .option("dbtable", "community_wordcloud") \
        .option("user", MYSQL_CONFIG["user"]) \
        .option("password", MYSQL_CONFIG["password"]) \
        .option("driver", MYSQL_CONFIG["driver"]) \
        .option("characterEncoding", "utf8") \
        .option("useUnicode", "true") \
        .mode("overwrite") \
        .save()

print(f"\n✅ 数据已写入MySQL表: community_wordcloud")
print(f"总计楼盘数: {len(community_names)}")
print(f"总计分词数: {len(all_words)}")
print(f"词云词条数: {len(top_words)}")

spark.stop()
