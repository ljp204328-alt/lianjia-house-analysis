"""用户接口（3 个）—— FastAPI 版，响应体与原 Django / Flask 版完全一致"""
import traceback

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from .auth import get_current_user, issue_token
from .models import create_user, find_user_by_username, verify_password

users_router = APIRouter(prefix="/users")


def _raise_bad_json(message, status=400):
    """与原版一致的错误 JSON：HTTP status + {"message", "code"}"""
    return JSONResponse(status_code=status, content={"message": message, "code": status})


async def _read_json(request: Request) -> dict:
    """读取 JSON body（对应原版 request.get_json(silent=True)）"""
    try:
        data = await request.json()
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


@users_router.post("/register/", status_code=201)
async def register(request: Request):
    """用户注册"""
    data = await _read_json(request)

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    password2 = data.get("password2") or ""
    phone = (data.get("phone") or "").strip() or None

    if not username:
        return _raise_bad_json("请输入用户名")
    if not password:
        return _raise_bad_json("请输入密码")
    if len(password) < 6:
        return _raise_bad_json("密码长度至少6位")
    if password != password2:
        return _raise_bad_json("两次密码不一致")
    if phone and (len(phone) != 11 or not phone.isdigit()):
        return _raise_bad_json("手机号格式不正确")

    if find_user_by_username(username):
        return _raise_bad_json("用户名已存在")

    create_user(username, password, phone)
    return {"message": "注册成功", "code": 200}


@users_router.post("/login/")
async def login(request: Request):
    """用户登录"""
    data = await _read_json(request)

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return _raise_bad_json("请提供用户名和密码")

    user = find_user_by_username(username)
    if not user or not verify_password(user, password):
        return _raise_bad_json("用户名或密码错误")

    return {
        "code": 200,
        "message": "登录成功",
        "data": {
            "token": issue_token(user["id"], user["username"]),
            "user_id": user["id"],
            "username": user["username"],
        },
    }


@users_router.get("/info/")
def user_info(user: dict = Depends(get_current_user)):
    """当前登录用户信息（token 校验失败时依赖层直接抛 401）"""
    return {
        "id": user["id"],
        "username": user["username"],
        "phone": user["phone"] or "",
        "avatar": None,
        "create_time": user["create_time"].strftime("%Y-%m-%d %H:%M:%S")
        if user["create_time"]
        else "",
    }
