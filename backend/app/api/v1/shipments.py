"""货运订单路由：CRUD + 状态流转 + 详情按币种合计。

筛选只提供 shipment_num 关键字与业务状态；不提供金额区间（spec）。
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import ChargeInfo, Shipment, User

router = APIRouter(prefix="/shipments", tags=["shipments"])

# 允许的业务状态流转（design D19）
TRANSITIONS = {
    ("draft", "confirmed"),
    ("draft", "cancelled"),
    ("confirmed", "completed"),
    ("confirmed", "cancelled"),
}


class ShipmentIn(BaseModel):
    shipment_num: str


class TransitionIn(BaseModel):
    pass


def _get_or_404(db: Session, sid: int) -> Shipment:
    s = db.get(Shipment, sid)
    if not s or s.status != 0:
        raise HTTPException(status_code=404, detail="该货运订单不存在")
    return s


def _totals(db: Session, shipment_id: int) -> dict:
    """单订单按币种合计（D13）：应付按 cost_currency、应收按 sell_currency 各自分组。"""
    def _group(col):
        return dict(
            db.query(col, func.sum(ChargeInfo.os_cost_amt if col is ChargeInfo.cost_currency else ChargeInfo.os_sell_amt))
            .filter(ChargeInfo.shipment_id == shipment_id, ChargeInfo.status == 0)
            .group_by(col)
            .all()
        )
    # 分两条查询，避免一次 GROUP BY 把两侧都按应付币种切分
    cost_rows = (
        db.query(ChargeInfo.cost_currency, func.sum(ChargeInfo.os_cost_amt))
        .filter(ChargeInfo.shipment_id == shipment_id, ChargeInfo.status == 0)
        .group_by(ChargeInfo.cost_currency)
        .all()
    )
    sell_rows = (
        db.query(ChargeInfo.sell_currency, func.sum(ChargeInfo.os_sell_amt))
        .filter(ChargeInfo.shipment_id == shipment_id, ChargeInfo.status == 0)
        .group_by(ChargeInfo.sell_currency)
        .all()
    )
    return {
        "cost_totals": [
            {"currency": r[0], "amount": f"{r[1] or 0:.2f}"} for r in cost_rows
        ],
        "sell_totals": [
            {"currency": r[0], "amount": f"{r[1] or 0:.2f}"} for r in sell_rows
        ],
    }


def _dto(s: Shipment, line_count=None, totals=None) -> dict:
    d = {
        "id": s.id,
        "shipment_num": s.shipment_num,
        "lifecycle": s.lifecycle,
        "status": s.status,
        "operator": s.operator,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }
    if line_count is not None:
        d["charge_info_count"] = line_count
    if totals is not None:
        d["cost_totals"] = totals["cost_totals"]
        d["sell_totals"] = totals["sell_totals"]
    return d


def _line_counts(db: Session, ids):
    from typing import Dict, List
    # type: (Session, List[int]) -> Dict[int, int]
    if not ids:
        return {}
    rows = (
        db.query(ChargeInfo.shipment_id, func.count(ChargeInfo.id))
        .filter(ChargeInfo.shipment_id.in_(ids), ChargeInfo.status == 0)
        .group_by(ChargeInfo.shipment_id)
        .all()
    )
    return dict(rows)


@router.get("")
def list_shipments(
    keyword: str = "",
    lifecycle: str = "",
    page: int = 1,
    page_size: int = 20,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Shipment).filter(Shipment.status == 0)
    if keyword:
        kw = keyword.strip().lower()
        # MySQL utf8mb4_0900_ai_ci 本就大小写不敏感；lower() 保证与预检语义一致
        q = q.filter(func.lower(Shipment.shipment_num).contains(kw))
    if lifecycle:
        q = q.filter(Shipment.lifecycle == lifecycle)
    total = q.count()
    items = (
        q.order_by(Shipment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    counts = _line_counts(db, [s.id for s in items])
    return {
        "items": [
            {
                "id": s.id,
                "shipment_num": s.shipment_num,
                "lifecycle": s.lifecycle,
                "status": s.status,
                "operator": s.operator,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                "charge_info_count": counts.get(s.id, 0),
            }
            for s in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", status_code=201)
def create_shipment(body: ShipmentIn, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    num = body.shipment_num.strip()
    if not num:
        raise HTTPException(status_code=422, detail="货运订单号必填")
    dup = (
        db.query(Shipment)
        .filter(func.lower(Shipment.shipment_num) == num.lower())
        .first()
    )
    if dup:
        raise HTTPException(status_code=409, detail="该货运订单号已被使用")
    s = Shipment(shipment_num=num, operator=user.phone)
    db.add(s)
    db.flush()
    return {"id": s.id, "shipment_num": s.shipment_num, "lifecycle": s.lifecycle,
            "operator": s.operator}


@router.patch("/{sid}")
def update_shipment(sid: int, body: ShipmentIn, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    s = _get_or_404(db, sid)
    num = body.shipment_num.strip()
    if not num:
        raise HTTPException(status_code=422, detail="货运订单号必填")
    dup = (
        db.query(Shipment)
        .filter(func.lower(Shipment.shipment_num) == num.lower(), Shipment.id != sid)
        .first()
    )
    if dup:
        raise HTTPException(status_code=409, detail="该货运订单号已被使用")
    s.shipment_num = num
    s.operator = user.phone
    return {"id": s.id, "shipment_num": s.shipment_num, "lifecycle": s.lifecycle,
            "operator": s.operator}


@router.delete("/{sid}")
def delete_shipment(sid: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    s = _get_or_404(db, sid)
    s.status = 1
    s.operator = user.phone
    return {"ok": True}


@router.get("/{sid}")
def get_shipment(sid: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = _get_or_404(db, sid)
    lines = (
        db.query(ChargeInfo)
        .filter(ChargeInfo.shipment_id == s.id, ChargeInfo.status == 0)
        .order_by(ChargeInfo.id)
        .all()
    )
    return {
        "id": s.id,
        "shipment_num": s.shipment_num,
        "lifecycle": s.lifecycle,
        "status": s.status,
        "operator": s.operator,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        "charge_info": [_line_dto(c) for c in lines],
        **_totals(db, s.id),
    }


def _money(v):
    """金额统一输出为两位小数字符串；None（关联记录未填侧）原样返回。"""
    from decimal import Decimal
    return f"{Decimal(v):.2f}" if v is not None else None


def _line_dto(c: ChargeInfo) -> dict:
    return {
        "id": c.id,
        "shipment_id": c.shipment_id,
        "job_num": c.job_num,
        "charge_code": c.charge_code,
        "department": c.department,
        "branch": c.branch,
        "cost_currency": c.cost_currency,
        "os_cost_amt": _money(c.os_cost_amt),
        "creditor": c.creditor,
        "sell_currency": c.sell_currency,
        "os_sell_amt": _money(c.os_sell_amt),
        "debtor": c.debtor,
        "related_source_id": c.related_source_id,
        "status": c.status,
        "operator": c.operator,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _transition(sid: int, target: str, user: User, db: Session):
    """单事务流转：行锁后校验矩阵（design D19），更新 lifecycle 与审计字段。"""
    s = (
        db.query(Shipment)
        .filter(Shipment.id == sid)
        .with_for_update()
        .first()
    )
    if not s or s.status != 0:
        raise HTTPException(status_code=404, detail="该货运订单不存在")
    if (s.lifecycle, target) not in TRANSITIONS:
        raise HTTPException(status_code=409, detail="该状态不允许此流转")
    s.lifecycle = target
    s.operator = user.phone
    return {"id": s.id, "shipment_num": s.shipment_num, "lifecycle": s.lifecycle,
            "operator": s.operator}


@router.post("/{sid}/confirm")
def confirm_shipment(sid: int, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    return _transition(sid, "confirmed", user, db)


@router.post("/{sid}/complete")
def complete_shipment(sid: int, user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    return _transition(sid, "completed", user, db)


@router.post("/{sid}/cancel")
def cancel_shipment(sid: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    return _transition(sid, "cancelled", user, db)
