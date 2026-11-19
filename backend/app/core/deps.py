"""FastAPI 依赖：认证与权限。

- get_current_user: 解析 Bearer 令牌，实时查库校验 is_active 与 status（D18 权限实时判定）
- require_admin: 在 get_current_user 之上判 authority

get_current_user 使用请求作用域的 get_db 会话：与业务查询同事务，
权限停用/变更在下一次请求即生效（每次都从库里读最新的 authority 与 is_active）。
"""
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未认证")
    token = auth.removeprefix("Bearer ").strip()
    try:
        phone = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="令牌无效或已过期")

    user = (
        db.query(User)
        .filter(User.phone == phone, User.is_active.is_(True), User.status == 0)
        .first()
    )
    if not user:
        raise HTTPException(status_code=401, detail="账号不可用")
    request.state.user = user
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.authority != "admin":
        raise HTTPException(status_code=403, detail="无权限")
    return user
