"""用户管理的请求体与响应体。"""
from typing import Optional

from fastapi import HTTPException
from pydantic import BaseModel, field_validator

from app.schemas.common import AuditOut


class UserIn(BaseModel):
    """新建与修改用户的载荷（手机号唯一，用户名称可重名）。"""

    phone: str
    username: str
    authority: str

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        if not (v.isdigit() and len(v) == 11):
            raise HTTPException(status_code=422, detail="手机号格式非法")
        return v

    @field_validator("username")
    @classmethod
    def check_username(cls, v: str) -> str:
        if not v.strip():
            raise HTTPException(status_code=422, detail="用户名称必填")
        return v.strip()


class AuthorityPatch(BaseModel):
    authority: str


class StatusIn(BaseModel):
    is_active: bool


class UserOut(AuditOut):
    """用户列表与详情中的用户记录。"""

    id: int
    phone: str
    username: str
    authority: str
    is_active: bool


class UserListOut(BaseModel):
    items: list[UserOut]
