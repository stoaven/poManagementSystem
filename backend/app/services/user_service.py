"""用户管理的业务规则：手机号唯一、权限级别枚举、不能停用自己。

路由只做取数与判权限，规则集中在这里，便于独立测试。
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import User

AUTHORITIES = ("admin", "normal")


def ensure_authority(authority: str) -> str:
    if authority not in AUTHORITIES:
        raise HTTPException(status_code=422, detail="权限级别无效")
    return authority


def ensure_phone_free(db: Session, phone: str, exclude_id: int = None) -> None:
    """手机号是唯一标识；重复报 409。"""
    q = db.query(User).filter(User.phone == phone)
    if exclude_id is not None:
        q = q.filter(User.id != exclude_id)
    if q.first():
        raise HTTPException(status_code=409, detail="该手机号已被使用")


def create_user(db: Session, phone: str, username: str, authority: str,
                actor: User) -> User:
    ensure_authority(authority)
    ensure_phone_free(db, phone)
    u = User(phone=phone, username=username, authority=authority,
             operator=actor.phone)
    db.add(u)
    db.flush()
    return u


def update_user(db: Session, user: User, phone: str, username: str,
                authority: str, actor: User) -> User:
    ensure_authority(authority)
    ensure_phone_free(db, phone, exclude_id=user.id)
    user.phone = phone
    user.username = username
    user.authority = authority
    user.operator = actor.phone
    return user


def set_active(db: Session, user: User, is_active: bool, actor: User) -> User:
    """启用停用；不能停用当前登录账号（否则系统可能失去最后一个管理员）。"""
    if user.id == actor.id and not is_active:
        raise HTTPException(status_code=409, detail="不能停用当前登录账号")
    user.is_active = is_active
    user.operator = actor.phone
    return user


def soft_delete(user: User, actor: User) -> User:
    user.status = 1
    user.operator = actor.phone
    return user
