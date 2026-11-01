"""
租金预测 Pipeline 模型加载器。

pkl 由 spark/ml/train_rent_model.py 训练产出，反序列化时依赖自定义
transformers 模块中的 4 个类。这里沿用原 Django 版的做法：
  1) 用 importlib 把 spark/ml/transformers.py 以 "transformers" 名字注册
     （避免与 HuggingFace transformers 库命名冲突）
  2) 同时挂到 __main__，供 Pipeline 反序列化查找

与原版的区别：模型只在首次使用时加载一次并缓存，
不再像原版那样每次预测都重新 joblib.load 18.5MB 文件。
"""
import importlib.util
import json
import os
import sys

import joblib

from config import BASE_DIR, Config

_TRANSFORMERS_DIR = os.path.join(BASE_DIR, "spark", "ml")
_TRANSFORMERS_PATH = os.path.join(_TRANSFORMERS_DIR, "transformers.py")


def _register_transformers():
    """把自定义 transformers 模块注册到 sys.modules 与 __main__"""
    if "transformers" in sys.modules:
        mod = sys.modules["transformers"]
    else:
        spec = importlib.util.spec_from_file_location("transformers", _TRANSFORMERS_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sys.modules["transformers"] = mod

    # Pipeline 反序列化时会去 __main__ 找这些类
    import __main__

    for name in (
        "LabelEncodeTransformer",
        "TargetEncodeTransformer",
        "AreaTransformer",
        "RentTypeAreaInteraction",
    ):
        setattr(sys.modules["transformers"], name, getattr(mod, name))
        setattr(__main__, name, getattr(mod, name))
    return mod


_register_transformers()

_pipeline = None
_metadata = None


def get_pipeline():
    """加载（并缓存）sklearn Pipeline"""
    global _pipeline
    if _pipeline is None:
        if not os.path.exists(Config.PIPELINE_PATH):
            raise FileNotFoundError(
                f"模型文件不存在: {Config.PIPELINE_PATH}，请先运行 spark/ml/train_rent_model.py"
            )
        _pipeline = joblib.load(Config.PIPELINE_PATH)
    return _pipeline


def get_metadata():
    """读取（并缓存）模型元数据"""
    global _metadata
    if _metadata is None:
        with open(Config.METADATA_PATH, "r", encoding="utf-8") as f:
            _metadata = json.load(f)
    return _metadata


def warmup():
    """启动时预热：加载模型与元数据，失败只告警不阻断服务"""
    try:
        get_pipeline()
        get_metadata()
        print("✓ 租金预测模型加载成功")
        return True
    except Exception as e:
        print(f"⚠ 租金预测模型加载失败（其余接口不受影响）: {e}")
        return False
