"""选项表的业务规则：code 一经创建不可修改、软删除、启停用、引用计数。

路由只做取数与判权限，规则集中在这里，便于独立测试。
"""
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ChargeInfo, User
from app.repositories.option import (
    KIND_TO_COLUMN,
    MODEL_BY_KIND,
    label_column,
)


def _model(kind: str):
    m = MODEL_BY_KIND.get(kind)
    if not m:
        raise HTTPException(status_code=404, detail="无效的选项类别")
    return m


def to_dict(o, referenced: int = 0) -> dict:
    """选项项 → 接口响应。

    标签按各自的列名返回：费用代码表是 description，其余五类是 name；
    标签省略时以 code 呈现。
    """
    d = {
        "id": o.id,
        "code": o.code,
        "name": None,
        "description": None,
        "is_active": o.is_active,
        "deleted": o.status == 1,
        "operator": o.operator,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "updated_at": o.updated_at.isoformat() if o.updated_at else None,
        "referenced": referenced,
    }
    col = label_column(type(o))
    d[col] = getattr(o, col) or o.code
    return d


def label_of(kind: str, body) -> Tuple[Optional[str], bool]:
    """从请求里取出该类选项的标签值，以及这次请求是否带了这个字段。

    费用代码表取 description，其余五类取 name——另一个字段被忽略。
    带上但值为空，是「清空标签」；没带，是「不改标签」，两者要分得开。
    """
    m = _model(kind)
    col = label_column(m)
    data = body.model_dump(exclude_unset=True)
    if col in data:
        return data[col], True
    return None, False


def reference_counts(db: Session, kind: str) -> Dict[str, int]:
    """一次分组查询拿到「每个取值被多少条未删除费用信息引用」。

    一类选项可能对应多列：币种同时出现在应付币种与应收币种上，任一侧引用都算。
    """
    cols = [getattr(ChargeInfo, name) for name in KIND_TO_COLUMN[kind]]
    counts: Dict[str, int] = {}
    for col in cols:
        rows = (
            db.query(col, func.count(ChargeInfo.id))
            .filter(ChargeInfo.status == 0, col.isnot(None))
            .group_by(col)
            .all()
        )
        for code, n in rows:
            counts[code] = counts.get(code, 0) + n
    return counts


def reference_count(db: Session, kind: str, code: str) -> int:
    """某个取值被多少条未删除费用信息引用。"""
    cols = [getattr(ChargeInfo, name) for name in KIND_TO_COLUMN[kind]]
    return (
        db.query(ChargeInfo)
        .filter(ChargeInfo.status == 0, *[col == code for col in cols])
        .count()
    )


def admin_list(db: Session, kind: str, include_deleted: bool = False) -> List[dict]:
    """管理列表（可含停用与已删除项），每项附带被引用的条数。"""
    m = _model(kind)
    q = db.query(m)
    if not include_deleted:
        q = q.filter(m.status == 0)
    rows = q.order_by(m.id).all()
    counts = reference_counts(db, kind)
    return [to_dict(o, counts.get(o.code, 0)) for o in rows]


def candidate_list(db: Session, kind: str, q: str = "") -> List[dict]:
    """候选列表（仅启用未删除），支持按 code/标签关键字过滤。"""
    m = _model(kind)
    query = db.query(m).filter(m.status == 0, m.is_active.is_(True))
    if q:
        # 费用代码表的标签列是 description，其余是 name——按各自那一列过滤
        label_col = getattr(m, label_column(m))
        query = query.filter(m.code.contains(q) | label_col.contains(q))
    return [to_dict(o) for o in query.order_by(m.code).all()]


def create(db: Session, kind: str, code: str, label: Optional[str],
           admin: User) -> dict:
    m = _model(kind)
    code = (code or "").strip()
    if not code:
        raise HTTPException(status_code=422, detail="缺少 code")
    if db.query(m).filter(m.code == code).first():
        raise HTTPException(status_code=409, detail="该代码已被使用")
    o = m(code=code, is_active=True, operator=admin.phone)
    setattr(o, label_column(m), label)
    db.add(o)
    db.flush()
    return to_dict(o)


def update(db: Session, kind: str, option_id: int, code: str,
           label: Optional[str], admin: User,
           label_provided: bool = True) -> dict:
    """只允许改标签（费用代码表是描述、其余是名称）；code 一经创建不可修改。

    label_provided 为假表示这次请求没带标签字段——保持原值不动；
    带上但传空则是清空标签，页面上会以代码呈现。
    """
    m = _model(kind)
    o = db.get(m, option_id)
    if not o or o.status != 0:
        raise HTTPException(status_code=404, detail="该选项不存在")
    if code and code.strip() and code.strip() != o.code:
        raise HTTPException(status_code=409, detail="代码不可修改")
    if label_provided:
        setattr(o, label_column(m), label)
    o.operator = admin.phone
    return to_dict(o)


def set_active(db: Session, kind: str, option_id: int, is_active: bool,
               admin: User) -> dict:
    """启用/停用。停用项不出现在候选列表，但仍可被费用信息引用。"""
    m = _model(kind)
    o = db.get(m, option_id)
    if not o or o.status != 0:
        raise HTTPException(status_code=404, detail="该选项不存在")
    o.is_active = is_active
    o.operator = admin.phone
    return to_dict(o)


def soft_delete(db: Session, kind: str, option_id: int,
                admin: User) -> Dict[str, object]:
    """软删除（status 置 1），返回删除前的引用数量。"""
    m = _model(kind)
    o = db.get(m, option_id)
    if not o or o.status != 0:
        raise HTTPException(status_code=404, detail="该选项不存在")
    ref_count = reference_count(db, kind, o.code)
    o.status = 1
    o.operator = admin.phone
    return {"ok": True, "referenced": ref_count}
