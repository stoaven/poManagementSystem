"""选项路由：六类共用一套端点，按 kind 分发。

candidates 必须注册在 /{kind} 之前，否则会被当成一个 kind 匹配掉（design D21）。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import (
    BranchOption,
    ChargeCode,
    ChargeInfo,
    Creditor,
    Currency,
    Debtor,
    Department,
    User,
)
from app.schemas.options import (
    OptionCandidatesOut,
    OptionDeleteOut,
    OptionIn,
    OptionListOut,
    OptionOut,
    OptionStatusIn,
    ReferencesOut,
)

router = APIRouter(prefix="/options", tags=["options"])

MODEL_MAP = {
    "charge_codes": ChargeCode,
    "departments": Department,
    "branches": BranchOption,
    "currencies": Currency,
    "creditors": Creditor,
    "debtors": Debtor,
}

# 费用信息表中与每类选项对应的取值列（引用计数用）。
# 一类选项可能对应多列：币种同时出现在应付币种与应收币种上。
CHARGE_COLUMN_MAP = {
    "charge_codes": ("charge_code",),
    "departments": ("department",),
    "branches": ("branch",),
    "currencies": ("cost_currency", "sell_currency"),
    "creditors": ("creditor",),
    "debtors": ("debtor",),
}


def _resolve(kind):
    m = MODEL_MAP.get(kind)
    if not m:
        raise HTTPException(status_code=404, detail="无效的选项类别")
    return m


def _dto(o, referenced: int = 0):
    return {
        "id": o.id,
        "code": o.code,
        "name": o.name or o.code,
        "is_active": o.is_active,
        "deleted": o.status == 1,
        "operator": o.operator,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "updated_at": o.updated_at.isoformat() if o.updated_at else None,
        "referenced": referenced,
    }


def _reference_counts(db: Session, kind: str) -> dict:
    """一次分组查询拿到「每个取值被多少条未删除费用信息引用」。"""
    cols = [getattr(ChargeInfo, name) for name in CHARGE_COLUMN_MAP[kind]]
    counts: dict = {}
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


@router.get("/candidates", response_model=OptionCandidatesOut)
def candidates(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """一次取回六类候选（启用且未删除）。"""
    result = {}
    for kind, m in MODEL_MAP.items():
        rows = db.query(m).filter(m.status == 0, m.is_active.is_(True)).all()
        result[kind] = [_dto(o) for o in rows]
    return {"kinds": result}


@router.get("/{kind}", response_model=OptionListOut)
def admin_list(kind: str, include_deleted: bool = False,
               _: User = Depends(require_admin), db: Session = Depends(get_db)):
    """管理列表（admin-only）。include_deleted=True 时包含已删除项。

    每一项附带被引用它未删除费用信息条数，供界面上直接显示。
    """
    m = _resolve(kind)
    q = db.query(m)
    if not include_deleted:
        q = q.filter(m.status == 0)
    rows = q.order_by(m.id).all()
    counts = _reference_counts(db, kind)
    return {"items": [_dto(o, counts.get(o.code, 0)) for o in rows]}


@router.get("/{kind}/options", response_model=OptionListOut)
def candidate_list(kind: str, q: str = "", _: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """候选列表（登录即可读），支持按 code/name 关键字过滤。"""
    m = _resolve(kind)
    query = db.query(m).filter(m.status == 0, m.is_active.is_(True))
    if q:
        query = query.filter(m.code.contains(q) | m.name.contains(q))
    rows = query.order_by(m.code).all()
    return {"items": [_dto(o) for o in rows]}


@router.post("/{kind}", status_code=201, response_model=OptionOut)
def create_option(kind: str, body: OptionIn, admin: User = Depends(require_admin),
                  db: Session = Depends(get_db)):
    m = _resolve(kind)
    code = body.code.strip()
    if not code:
        raise HTTPException(status_code=422, detail="缺少 code")
    if db.query(m).filter(m.code == code).first():
        raise HTTPException(status_code=409, detail="该代码已被使用")
    o = m(code=code, name=body.name, is_active=True, operator=admin.phone)
    db.add(o)
    db.flush()
    return _dto(o)


@router.patch("/{kind}/{option_id}", response_model=OptionOut)
def update_option(kind: str, option_id: int, body: OptionIn,
                  admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """编辑：只允许改名称；code 一经创建不可修改。"""
    m = _resolve(kind)
    o = db.get(m, option_id)
    if not o or o.status != 0:
        raise HTTPException(status_code=404, detail="该选项不存在")
    if body.code and body.code.strip() and body.code.strip() != o.code:
        raise HTTPException(status_code=409, detail="代码不可修改")
    o.name = body.name if body.name is not None else o.name
    o.operator = admin.phone
    return _dto(o)


@router.patch("/{kind}/{option_id}/status", response_model=OptionOut)
def set_option_status(kind: str, option_id: int, body: OptionStatusIn,
                      admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """启用/停用。停用项不出现在候选列表，但仍可被费用信息引用。"""
    m = _resolve(kind)
    o = db.get(m, option_id)
    if not o or o.status != 0:
        raise HTTPException(status_code=404, detail="该选项不存在")
    o.is_active = body.is_active
    o.operator = admin.phone
    return _dto(o)


def _reference_count(db: Session, kind: str, code: str) -> int:
    """统计引用该选项的未删除费用信息条数。

    币种同时用于应付与应收两侧，任一侧引用都算引用。
    """
    cols = [getattr(ChargeInfo, name) for name in CHARGE_COLUMN_MAP[kind]]
    return (
        db.query(ChargeInfo)
        .filter(
            ChargeInfo.status == 0,
            *[col == code for col in cols],
        )
        .count()
    )


@router.get("/{kind}/{option_id}/references", response_model=ReferencesOut)
def option_references(kind: str, option_id: int, _: User = Depends(require_admin),
                       db: Session = Depends(get_db)):
    """删除前的引用数量预检（spec：删除前告知引用条数）。"""
    m = _resolve(kind)
    o = db.get(m, option_id)
    if not o or o.status != 0:
        raise HTTPException(status_code=404, detail="该选项不存在")
    return {"referenced": _reference_count(db, kind, o.code)}


@router.delete("/{kind}/{option_id}", response_model=OptionDeleteOut)
def delete_option(kind: str, option_id: int, admin: User = Depends(require_admin),
                  db: Session = Depends(get_db)):
    """软删除：status 置 1，返回删除前的引用数量。"""
    m = _resolve(kind)
    o = db.get(m, option_id)
    if not o or o.status != 0:
        raise HTTPException(status_code=404, detail="该选项不存在")
    ref_count = _reference_count(db, kind, o.code)
    o.status = 1
    o.operator = admin.phone
    return {"ok": True, "referenced": ref_count}
