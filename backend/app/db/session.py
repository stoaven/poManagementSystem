"""数据库会话管理：engine、sessionmaker、get_db 依赖。

一个请求一个事务：get_db 在请求结束时 commit（成功）或 rollback（失败），
service 层不自行 commit（design D22/任务 2.6）。
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：一个请求一个事务。

    注意：except 分支必须重新抛出原异常——吞掉它会让 FastAPI 收不到响应，
    表现为 500 且日志里只有 "No response object was returned"。
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
