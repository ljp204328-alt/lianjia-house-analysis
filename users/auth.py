"""JWT 签发 / 校验（PyJWT 手工实现，替代 Flask-JWT-Extended）

前端要求 header 为 `Authorization: Token <payload>`（不是 Bearer），
故这里手工解析前缀，保持与原 Django / Flask 版行为一致。
"""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Request

from config import Config
from .models import find_user_by_id

_TOKEN_PREFIX = "Token "


def issue_token(user_id: int, username: str) -> str:
    """为用户签发访问令牌（sub 存用户 id 字符串，兼容原 JWT identity）"""
    return jwt.encode(
        {
            "sub": str(user_id),
            "username": username,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc)
            + timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES),
        },
        Config.JWT_SECRET_KEY,
        algorithm="HS256",
    )


def get_current_user(request: Request) -> dict:
    """校验 `Authorization: Token xxx`，返回用户记录；失败抛 401"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith(_TOKEN_PREFIX):
        raise HTTPException(status_code=401, detail="未登录或登录已过期")

    token = auth[len(_TOKEN_PREFIX):].strip()
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")

    try:
        user_id = int(payload.get("sub", ""))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="未登录或登录已过期")

    user = find_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user
