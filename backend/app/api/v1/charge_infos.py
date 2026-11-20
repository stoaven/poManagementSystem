"""费用信息路由：创建 / 编辑 / 软删除 / 关联生成。

关联生成（design D13）：
- 源 Branch=SHL 且 Debtor=CNSHO -> 关联记录 Branch=SHO、Creditor=CNSHL、
  应付币种/金额取源记录的应收侧
- 源 Branch=SHO 且 Creditor=CNSHL -> 关联记录 Branch=SHL、Debtor=CNSHO、
  应收币种/金额取源记录的应付侧
- 费用代码与应付部门复制源记录；未填写的一侧留空
- 关联记录（related_source_id 非空）不能再生成关联记录
"""
from decimal import Decimal, InvalidOperation


def _money(v):
    """金额统一输出为两位小数字符串；None（关联记录未填侧）原样返回。"""
    return f"{Decimal(v):.2f}" if v is not None else None
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import ChargeInfo, Shipment, User
from app.repositories.option import validate_option_value
from app.schemas.charge_info import ChargeInfoIn, ChargeInfoOut, ChargeInfoPatch
from app.schemas.common import OkOut

router = APIRouter(tags=["charge-info"])

MAX_AMT = Decimal("999999999999.99")

# 六类选项与费用信息字段的对应（category field -> option kind）
FIELD_KIND = {
    "charge_code": "charge_codes",
    "department": "departments",
    "branch": "branches",
    "cost_currency": "currencies",
    "creditor": "creditors",
    "sell_currency": "currencies",
    "debtor": "debtors",
}

RELATED_RULES = {
    ("SHL", "CNSHO"): {"branch": "SHO", "creditor": "CNSHL"},
    ("SHO", "CNSHL"): {"branch": "SHL", "debtor": "CNSHO"},
}


def _check_amount(name: str, value: str) -> Decimal:
    try:
        amt = Decimal(value)
    except (InvalidOperation, TypeError):
        raise HTTPException(status_code=422, detail=f"{name} 不是有效金额")
    if amt < 0:
        raise HTTPException(status_code=422, detail="金额不能为负")
    if amt > MAX_AMT:
        raise HTTPException(status_code=422, detail="金额超出上限")
    if -amt.as_tuple().exponent > 2:
        raise HTTPException(status_code=422, detail="金额最多两位小数")
    return amt


def _get_line_or_404(db: Session, line_id: int) -> ChargeInfo:
    c = db.get(ChargeInfo, line_id)
    if not c or c.status != 0:
        raise HTTPException(status_code=404, detail="该费用信息不存在")
    return c


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
        "operator": c.operator,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _validate_options(db: Session, data: dict, existing: Optional[ChargeInfo] = None):
    """七个分类字段对照选项表校验（三态：不存在/已停用/已删除）。"""
    for field, kind in FIELD_KIND.items():
        value = data.get(field)
        if value is None:
            continue  # 留空交给必填校验
        validate_option_value(db, kind, value,
                              editing=existing is not None,
                              unchanged=(existing is not None and getattr(existing, field) == value))


@router.post("/shipments/{sid}/charge-infos", status_code=201, response_model=ChargeInfoOut)
def create_charge_info(sid: int, body: ChargeInfoIn,
                       user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.get(Shipment, sid)
    if not s or s.status != 0:
        raise HTTPException(status_code=404, detail="该货运订单不存在")
    data = body.model_dump()
    _check_amount("应付金额", data["os_cost_amt"])
    _check_amount("应收金额", data["os_sell_amt"])
    _validate_options(db, data)
    c = ChargeInfo(shipment_id=s.id, job_num=s.shipment_num,
                   operator=user.phone, **data)
    db.add(c)
    db.flush()
    return _line_dto(c)


@router.patch("/charge-infos/{line_id}", response_model=ChargeInfoOut)
def update_charge_info(line_id: int, body: ChargeInfoPatch,
                       user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = _get_line_or_404(db, line_id)
    data = body.model_dump(exclude_none=True)
    for name in ("os_cost_amt", "os_sell_amt"):
        if name in data:
            _check_amount("应付金额" if name == "os_cost_amt" else "应收金额", data[name])
    _validate_options(db, data, existing=c)
    for k, v in data.items():
        setattr(c, k, v)
    c.operator = user.phone
    return _line_dto(c)


@router.delete("/charge-infos/{line_id}", response_model=OkOut)
def delete_charge_info(line_id: int, user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    c = _get_line_or_404(db, line_id)
    c.status = 1
    c.operator = user.phone
    return {"ok": True}


@router.post("/charge-infos/{line_id}/related", status_code=201, response_model=ChargeInfoOut)
def create_related(line_id: int, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """由源记录生成关联记录。关联记录本身（related_source_id 非空）不能再生成。"""
    src = _get_line_or_404(db, line_id)
    if src.related_source_id is not None:
        raise HTTPException(status_code=409, detail="关联生成的记录不能再生成关联记录")

    rule = RELATED_RULES.get((src.branch, src.debtor))
    if rule:
        new = ChargeInfo(
            shipment_id=src.shipment_id, job_num=src.job_num,
            charge_code=src.charge_code, department=src.department,
            branch=rule["branch"], creditor=rule["creditor"],
            cost_currency=src.sell_currency, os_cost_amt=src.os_sell_amt,
            sell_currency=None, os_sell_amt=None, debtor=None,
            related_source_id=src.id, operator=user.phone,
        )
    elif (src.branch, src.creditor) == ("SHO", "CNSHL"):
        new = ChargeInfo(
            shipment_id=src.shipment_id, job_num=src.job_num,
            charge_code=src.charge_code, department=src.department,
            branch="SHL", creditor=None,
            cost_currency=None, os_cost_amt=None,
            sell_currency=src.cost_currency, os_sell_amt=src.os_cost_amt,
            debtor="CNSHO",
            related_source_id=src.id, operator=user.phone,
        )
    else:
        raise HTTPException(status_code=409, detail="该记录不满足关联生成条件")
    db.add(new)
    db.flush()
    return _line_dto(new)
