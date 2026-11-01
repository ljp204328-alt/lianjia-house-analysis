import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 真实凭据只能放在项目根目录的 .env（已被 .gitignore 排除，不会上传仓库）
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    """全局配置：敏感信息一律从 .env 读取，缺项直接报错提示"""

    # ================= 业务数据库（虚拟机，17 张分析结果表） =================
    BUSINESS_DB_HOST = os.getenv("BUSINESS_DB_HOST")
    BUSINESS_DB_PASSWORD = os.getenv("BUSINESS_DB_PASSWORD")
    MYSQL_CONFIG = {
        "host": BUSINESS_DB_HOST,
        "port": int(os.getenv("BUSINESS_DB_PORT", "3306")),
        "user": os.getenv("BUSINESS_DB_USER", "root"),
        "password": BUSINESS_DB_PASSWORD,
        "database": os.getenv("BUSINESS_DB_NAME", "lianjia_analysis"),
        "charset": "utf8mb4",
        "connect_timeout": 10,
    }

    # ================= 用户数据库（本机，用户账号） =================
    USER_DB_HOST = os.getenv("USER_DB_HOST", "localhost")
    USER_DB_PORT = int(os.getenv("USER_DB_PORT", "3306"))
    USER_DB_USER = os.getenv("USER_DB_USER", "root")
    USER_DB_PASSWORD = os.getenv("USER_DB_PASSWORD")
    USER_DB_NAME = os.getenv("USER_DB_NAME", "zufangdata")

    # ================= JWT =================
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    # 前端发送的是 "Authorization: Token xxx"，不是默认的 "Bearer xxx"
    # （users/auth.py 按此前缀手工解析）
    JWT_HEADER_TYPE = "Token"
    # 登录有效期 7 天
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 24 * 7

    # ================= 服务 =================
    HOST = os.getenv("API_HOST", "0.0.0.0")
    PORT = int(os.getenv("API_PORT", "8000"))

    # ================= 接口缓存（秒） =================
    CACHE_TTL = 300

    # ================= 机器学习模型 =================
    MODEL_DIR = os.path.join(BASE_DIR, "spark", "ml", "model")
    PIPELINE_PATH = os.path.join(MODEL_DIR, "pipeline_model.pkl")
    METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.json")


_REQUIRED_ENV = [
    "BUSINESS_DB_HOST",
    "BUSINESS_DB_PASSWORD",
    "USER_DB_PASSWORD",
    "JWT_SECRET_KEY",
]
_missing = [
    k for k in _REQUIRED_ENV
    if not getattr(Config, k)
]
if _missing:
    raise RuntimeError(
        "缺少配置项，请复制 .env.example 为 .env 并填写: " + ", ".join(_missing)
    )
