"""SQLAlchemy DeclarativeBase 与公共 Mixin / users 模型。

所有表统一携带四个字段（见 design D9/D26）：
- status: 0 正常 / 1 已删除（软删除标记）
- operator: 操作人手机号，FK -> users.phone，带 ON UPDATE CASCADE
- created_at / updated_at: 创建时间与更新时间（更新或删除的时刻）
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditMixin:
    """status + operator + created_at + updated_at 四件套。"""

    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0"
    )
    operator: Mapped[str] = mapped_column(
        String(20), ForeignKey("users.phone", onupdate="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class User(Base):
    """users 表（operator 可空：首个管理员由 CLI 创建，无操作人）。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    username: Mapped[str] = mapped_column(String(64))
    authority: Mapped[str] = mapped_column(
        String(10), nullable=False, default="normal", server_default="normal"
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="1")
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0"
    )
    operator: Mapped[Optional[str]] = mapped_column(
        String(20), ForeignKey("users.phone", onupdate="CASCADE"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
