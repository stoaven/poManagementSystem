"""认证相关的请求体与响应体。"""
from pydantic import BaseModel


class LoginIn(BaseModel):
    """登录请求：只提交手机号，无密码无验证码（design D17）。"""

    phone: str


class UserBrief(BaseModel):
    """当前用户的简要信息。"""

    id: int
    phone: str
    username: str
    authority: str


class LoginOut(BaseModel):
    token: str
    user: UserBrief


class MeOut(UserBrief):
    """/auth/me 的响应：与登录返回的 user 同一形状。"""
