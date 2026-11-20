"""认证路由：手机号登录（无密码无验证码）。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_token
from app.db.session import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    phone: str


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(User.phone == body.phone, User.is_active.is_(True), User.status == 0)
        .first()
    )
    if not user:
        raise HTTPException(status_code=401, detail="该手机号未开通账号")
    return {
        "token": create_token(user.phone),
        "user": {
            "id": user.id,
            "phone": user.phone,
            "username": user.username,
            "authority": user.authority,
        },
    }


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "phone": user.phone,
        "username": user.username,
        "authority": user.authority,
    }
