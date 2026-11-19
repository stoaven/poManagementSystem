"""用户管理路由（全部 admin-only）。"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])


class UserIn(BaseModel):
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


def _dto(u: User) -> dict:
    return {
        "id": u.id,
        "phone": u.phone,
        "username": u.username,
        "authority": u.authority,
        "is_active": u.is_active,
        "status": u.status,
        "operator": u.operator,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "updated_at": u.updated_at.isoformat() if u.updated_at else None,
    }


def _get_or_404(db: Session, user_id: int) -> User:
    u = db.get(User, user_id)
    if not u or u.status != 0:
        raise HTTPException(status_code=404, detail="该用户不存在")
    return u


@router.get("")
def list_users(
    keyword: str = "",
    authority: str = "",
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(User).filter(User.status == 0)
    if keyword:
        kw = keyword.strip()
        q = q.filter(User.phone.contains(kw) | User.username.contains(kw))
    if authority:
        q = q.filter(User.authority == authority)
    return {"items": [_dto(u) for u in q.order_by(User.id).all()]}


@router.post("", status_code=201)
def create_user(body: UserIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.query(User).filter(User.phone == body.phone).first():
        raise HTTPException(status_code=409, detail="该手机号已被使用")
    if body.authority not in ("admin", "normal"):
        raise HTTPException(status_code=422, detail="权限级别无效")
    u = User(phone=body.phone, username=body.username, authority=body.authority,
             operator=admin.phone)
    db.add(u)
    db.flush()
    return _dto(u)


@router.patch("/{user_id}")
def update_user(
    user_id: int, body: UserIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    u = _get_or_404(db, user_id)
    if body.authority not in ("admin", "normal"):
        raise HTTPException(status_code=422, detail="权限级别无效")
    dup = db.query(User).filter(User.phone == body.phone, User.id != user_id).first()
    if dup:
        raise HTTPException(status_code=409, detail="该手机号已被使用")
    u.phone = body.phone
    u.username = u.username if False else body.username
    u.authority = body.authority
    u.operator = admin.phone
    return _dto(u)


@router.patch("/{user_id}/status")
def set_status(
    user_id: int, body: StatusIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    u = _get_or_404(db, user_id)
    if u.id == admin.id and not body.is_active:
        raise HTTPException(status_code=409, detail="不能停用当前登录账号")
    u.is_active = body.is_active
    u.operator = admin.phone
    return _dto(u)


@router.delete("/{user_id}")
def delete_user(user_id: int, admin: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if admin.authority != "admin":
        raise HTTPException(status_code=403, detail="无权限")
    u = _get_or_404(db, user_id)
    u.status = 1
    u.operator = admin.phone
    return {"ok": True}
