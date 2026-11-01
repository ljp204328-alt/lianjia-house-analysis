"""
FastAPI 后端入口。

启动：python app.py
接口前缀：
  /analysis/api/*   16 个数据分析接口（公开）
  /users/*          注册 / 登录 / 用户信息（info 需登录）
  /ai/*             AI 智能体问答（chat 需登录）
"""
import sys

# Windows 控制台默认 GBK，强制 UTF-8 避免 print 中文/符号崩溃
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import Config

app = FastAPI(
    title="链家租房数据分析系统 API",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# 前端 request.js 走绝对地址跨域直连，允许任意来源即可（不用 credentials）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from analysis import analysis_router  # noqa: E402
from ai import ai_router  # noqa: E402
from users import users_router  # noqa: E402

app.include_router(analysis_router)
app.include_router(users_router)
app.include_router(ai_router)


# ---- 统一错误响应（保持原 Flask 版格式） ----
@app.exception_handler(StarletteHTTPException)
async def http_exc_handler(request: Request, exc: StarletteHTTPException):
    code = exc.status_code
    if code == 404:
        body = {"error": "接口不存在"}
    elif code == 405:
        body = {"error": "请求方法不允许"}
    elif code == 401:
        body = {"message": exc.detail or "未登录或登录已过期", "code": 401}
    elif code == 500:
        body = {"error": "服务器内部错误"}
    else:
        body = {"error": str(exc.detail) if exc.detail else "请求失败"}
    return JSONResponse(status_code=code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"error": "请求参数错误"})


@app.exception_handler(Exception)
async def all_exc_handler(request: Request, exc: Exception):
    import traceback

    traceback.print_exc()
    return JSONResponse(status_code=500, content={"error": "服务器内部错误"})


@app.get("/")
def index():
    return {
        "name": "链家租房数据分析系统 API",
        "framework": "FastAPI",
        "endpoints": {
            "analysis": "/analysis/api/*",
            "users": "/users/register/ /users/login/ /users/info/",
            "ai": "/ai/chat/",
        },
    }


def _startup():
    """启动前准备：建用户表 + 预热模型"""
    from users.models import init_users_table

    try:
        init_users_table()
        print("✓ 用户表就绪")
    except Exception as e:
        print(f"⚠ 用户表初始化失败（注册/登录不可用）: {e}")

    from analysis.model_loader import warmup

    warmup()


if __name__ == "__main__":
    import uvicorn

    _startup()
    print(f"后端启动: http://{Config.HOST}:{Config.PORT}  (FastAPI + Uvicorn)")
    print(f"业务库: {Config.MYSQL_CONFIG['host']}/{Config.MYSQL_CONFIG['database']}")
    print(f"用户库: {Config.USER_DB_HOST}/{Config.USER_DB_NAME}")
    uvicorn.run(app, host=Config.HOST, port=Config.PORT, log_level="info")
