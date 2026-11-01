"""
租金价格预测模型训练脚本（Pipeline版本）
从Hive读取清洗后的租房数据，训练随机森林回归模型，保存为pkl文件
"""
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os
import json
import sys

# 添加当前目录到路径，以便导入transformers模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from transformers import LabelEncodeTransformer, TargetEncodeTransformer, AreaTransformer, RentTypeAreaInteraction

# ================= 配置区域 =================
SPARK_MASTER_URL = "spark://hadoop:7077"
METASTORE_URI = "thrift://hadoop:9083"
SRC_DB = "default"
SRC_TABLE = "dwd_lianjia_house_clean"

# 特征列和目标列
FEATURE_COLS = ["city", "district", "house_type", "area", "direction", "floor_type", "rent_type"]
TARGET_COL = "price"

# 模型保存路径
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")
PIPELINE_PATH = os.path.join(MODEL_DIR, "pipeline_model.pkl")
METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.json")


# ================= 主函数 =================

def main():
    print("=" * 50)
    print("租金价格预测模型 - Pipeline版本")
    print("=" * 50)

    # 1. 启动Spark，读取Hive数据
    spark = (
        SparkSession.builder
        .appName("Rent_Price_Model_Training_Pipeline")
        .master(SPARK_MASTER_URL)
        .enableHiveSupport()
        .config("spark.sql.adaptive.enabled", "false")
        .getOrCreate()
    )

    try:
        print(f"\n【1】读取Hive数据: {SRC_DB}.{SRC_TABLE}")
        df = spark.table(f"{SRC_DB}.{SRC_TABLE}")

        # 只选取需要的列
        df_select = df.select(*FEATURE_COLS, TARGET_COL)

        # 过滤无效数据
        df_select = df_select.filter(
            F.col("area").isNotNull() &
            (F.col("area") > 0) &
            F.col("price").isNotNull() &
            (F.col("price") > 0)
        )

        total_count = df_select.count()
        print(f"  有效数据量: {total_count} 条")

        # 过滤掉rent_type为"不限"的数据
        df_select = df_select.filter(F.col("rent_type").isin("整租", "合租"))
        after_filter = df_select.count()
        print(f"  过滤'不限'后: {after_filter} 条 (删除 {total_count - after_filter} 条)")

        # 2. 转换为Pandas DataFrame
        print("\n【2】转换为Pandas DataFrame")
        pdf = df_select.toPandas()
        print(f"  数据形状: {pdf.shape}")

        # 3. 划分特征和目标
        print("\n【3】划分特征和目标")
        X = pdf[FEATURE_COLS]
        y = pdf[TARGET_COL]

        # 4. 划分训练集和测试集
        print("\n【4】划分训练集/测试集")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        print(f"  训练集: {len(X_train)} 条")
        print(f"  测试集: {len(X_test)} 条")

        # 5. 定义列处理器
        print("\n【5】构建Pipeline")
        
        # Label编码列
        label_encode_cols = ["house_type", "direction", "floor_type"]
        # 目标编码列
        target_encode_cols = ["city", "district"]
        # 数值列
        numeric_cols = ["area"]
        # 交互特征列
        interaction_cols = ["rent_type", "area"]

        # 预处理器
        preprocessor = ColumnTransformer(
            transformers=[
                ('label', LabelEncodeTransformer(), label_encode_cols),
                ('target', TargetEncodeTransformer(), target_encode_cols),
                ('area', AreaTransformer(), numeric_cols),
                ('rent_area', RentTypeAreaInteraction(), interaction_cols)
            ],
            remainder='drop'  # 丢弃未处理的列（rent_type不再单独出现）
        )

        # 完整Pipeline
        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('model', RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ))
        ])

        print("  Pipeline构建完成！")

        # 6. 训练模型
        print("\n【6】训练Pipeline")
        pipeline.fit(X_train, y_train)
        print("  训练完成！")

        # 7. 模型评估
        print("\n【7】模型评估")
        y_pred_train = pipeline.predict(X_train)
        y_pred_test = pipeline.predict(X_test)

        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)

        print(f"  训练集 MAE: {train_mae:.2f} 元")
        print(f"  测试集 MAE: {test_mae:.2f} 元")
        print(f"  训练集 R²:  {train_r2:.4f}")
        print(f"  测试集 R²:  {test_r2:.4f}")

        # 特征重要性
        print("\n  特征重要性:")
        importance = pipeline.named_steps['model'].feature_importances_
        actual_feature_names = label_encode_cols + target_encode_cols + numeric_cols + ["rent_type_area"]
        for name, imp in sorted(zip(actual_feature_names, importance), key=lambda x: -x[1]):
            print(f"    {name}: {imp:.4f}")

        # 8. 保存Pipeline
        print(f"\n【8】保存Pipeline到: {PIPELINE_PATH}")
        os.makedirs(MODEL_DIR, exist_ok=True)

        # 保存整个Pipeline（一个文件搞定！）
        joblib.dump(pipeline, PIPELINE_PATH)

        # 获取编码信息用于元数据
        label_encoder = pipeline.named_steps['preprocessor'].named_transformers_['label']
        target_encoder = pipeline.named_steps['preprocessor'].named_transformers_['target']
        rent_area_interaction = pipeline.named_steps['preprocessor'].named_transformers_['rent_area']

        # 保存元数据
        metadata = {
            "feature_cols": actual_feature_names,
            "label_encode_cols": label_encode_cols,
            "target_encode_cols": target_encode_cols,
            "numeric_cols": numeric_cols,
            "interaction_cols": interaction_cols,
            "test_mae": float(test_mae),
            "test_r2": float(test_r2),
            "train_count": len(X_train),
            "test_count": len(X_test),
            "total_count": total_count,
            "encoder_classes": label_encoder.get_encoder_classes(),
            "target_maps": target_encoder.get_maps(),
            "rent_type_classes": rent_area_interaction.rent_type_encoder.classes_.tolist(),
            "global_mean": float(y.mean())
        }
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"  Pipeline文件: {PIPELINE_PATH}")
        print(f"  元数据文件: {METADATA_PATH}")

        print("\n" + "=" * 50)
        print("训练完成！Pipeline已保存")
        print("=" * 50)

    except Exception as e:
        print(f"训练失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
