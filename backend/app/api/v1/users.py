"""用户管理路由（全部 admin-only）。

路由只做取数与判权限，业务规则在 `app/services/user_service.py`。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import User
from app.schemas.common import OkOut
from app.schemas.users import StatusIn, UserIn, UserListOut, UserOut
from app.services import user_service as svc

router = APIRouter(prefix="/users", tags=["users"])


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


@router.get("", response_model=UserListOut)
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


@router.post("", status_code=201, response_model=UserOut)
def create_user(body: UserIn, admin: User = Depends(require_admin),
                db: Session = Depends(get_db)):
    u = svc.create_user(db, body.phone, body.username, body.authority, admin)
    return _dto(u)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserIn, admin: User = Depends(require_admin),
                db: Session = Depends(get_db)):
    u = _get_or_404(db, user_id)
    svc.update_user(db, u, body.phone, body.username, body.authority, admin)
    return _dto(u)


@router.patch("/{user_id}/status", response_model=UserOut)
def set_status(user_id: int, body: StatusIn, admin: User = Depends(require_admin),
               db: Session = Depends(get_db)):
    u = _get_or_404(db, user_id)
    svc.set_active(db, u, body.is_active, admin)
    return _dto(u)


@router.delete("/{user_id}", response_model=OkOut)
def delete_user(user_id: int, admin: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    if admin.authority != "admin":
        raise HTTPException(status_code=403, detail="无权限")
    u = _get_or_404(db, user_id)
    svc.soft_delete(u, admin)
    return {"ok": True}
