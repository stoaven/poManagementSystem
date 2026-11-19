"""JWT 签发与校验（无密码哈希——本系统以手机号为凭证，见 design D17/D20）。"""
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings


def create_token(phone: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": phone,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> str:
    """校验令牌，返回手机号；无效或过期抛 jwt.PyJWTError。"""
    settings = get_settings()
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    return payload["sub"]


def is_valid_phone(phone: str) -> bool:
    """11 位数字（中国大陆手机号）。"""
    return phone.isdigit() and len(phone) == 11
