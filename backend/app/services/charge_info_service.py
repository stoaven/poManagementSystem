"""费用信息的业务规则：成对写入、金额约束、分类字段取值校验。

**新增一条费用信息会写入两条记录**（design D30）：

页面填写的 9 个字段被拆到两条记录里——

| | A（应付侧那条） | B（镜像分支那条） |
|---|---|---|
| charge_code | 页面 | 页面 |
| department | 页面 | = A.department |
| branch | 页面 | 镜像分支（SHL↔SHO） |
| cost_currency | 页面 | = A.sell_currency |
| os_cost_amt | 页面 | = A.os_sell_amt |
| creditor | 页面 | 对家单位 |
| sell_currency | = A.cost_currency | 页面 |
| os_sell_amt | = A.os_cost_amt | 页面 |
| debtor | 对家单位 | 页面 |

「对家单位」按当前分支定：SHL 的对家是 CNSHO，SHO 的对家是 CNSHL。
"""
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import ChargeInfo, Shipment, User
from app.repositories.option import validate_option_value

MAX_AMT = Decimal("999999999999.99")

# 当前分支机构 -> 镜像分支
BRANCH_MIRROR = {"SHL": "SHO", "SHO": "SHL"}

# 当前分支机构 -> 对家单位（A 的应收对象，也是 B 的应付对象）
COUNTERPARTY = {"SHL": "CNSHO", "SHO": "CNSHL"}

# 六个选项类别与费用信息字段的对应（category field -> option kind）
FIELD_KIND = {
    "charge_code": "charge_codes",
    "department": "departments",
    "branch": "branches",
    "cost_currency": "currencies",
    "creditor": "creditors",
    "sell_currency": "currencies",
    "debtor": "debtors",
}

def money_text(value) -> Optional[str]:
    """金额统一输出为两位小数字符串；None（关联记录未填侧）原样返回。"""
    return f"{Decimal(value):.2f}" if value is not None else None


def line_to_dict(c: ChargeInfo) -> dict:
    """费用信息记录 → 接口响应。"""
    return {
        "id": c.id,
        "shipment_id": c.shipment_id,
        "job_num": c.job_num,
        "charge_code": c.charge_code,
        "department": c.department,
        "branch": c.branch,
        "cost_currency": c.cost_currency,
        "os_cost_amt": money_text(c.os_cost_amt),
        "creditor": c.creditor,
        "sell_currency": c.sell_currency,
        "os_sell_amt": money_text(c.os_sell_amt),
        "debtor": c.debtor,
        "status": c.status,
        "operator": c.operator,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def check_amount(name: str, value) -> Decimal:
    """金额约束：合法数字、非负、最多两位小数、不超上限。"""
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


def validate_options(db: Session, data: dict,
                     existing: Optional[ChargeInfo] = None) -> None:
    """分类字段对照选项表校验（三态：不存在 / 已停用 / 已删除）。"""
    for field, kind in FIELD_KIND.items():
        value = data.get(field)
        if value is None:
            continue  # 留空交给必填校验
        validate_option_value(db, kind, value,
                              editing=existing is not None,
                              unchanged=(existing is not None
                                         and getattr(existing, field) == value))


def build_pair(data: dict) -> Tuple[dict, dict]:
    """按规则算出要写入的两条费用信息（A 与 B）。"""
    branch = data["branch"]
    if branch not in BRANCH_MIRROR:
        raise HTTPException(
            status_code=422,
            detail=f"分支机构 {branch} 没有对应的镜像分支，目前只支持 SHL 与 SHO",
        )
    counterpart = COUNTERPARTY[branch]

    # A：页面填的应付侧 + 由应付侧推出的应收侧
    a = {
        "charge_code": data["charge_code"],
        "department": data["department"],
        "branch": branch,
        "cost_currency": data["cost_currency"],
        "os_cost_amt": data["os_cost_amt"],
        "creditor": data["creditor"],
        "sell_currency": data["cost_currency"],
        "os_sell_amt": data["os_cost_amt"],
        "debtor": counterpart,
    }
    # B：由 A 推出的应付侧 + 页面填的应收侧
    b = {
        "charge_code": a["charge_code"],
        "department": a["department"],
        "branch": BRANCH_MIRROR[branch],
        "cost_currency": a["sell_currency"],
        "os_cost_amt": a["os_sell_amt"],
        "creditor": counterpart,
        "sell_currency": data["sell_currency"],
        "os_sell_amt": data["os_sell_amt"],
        "debtor": data["debtor"],
    }
    return a, b


def create_pair(db: Session, shipment: Shipment, data: dict,
                user: User) -> List[ChargeInfo]:
    """新增费用信息：一次写入 A、B 两条记录。

    两条都在同一个事务里：任一条校验不过，两条都不落库。
    """
    a, b = build_pair(data)
    for d in (a, b):
        check_amount("应付金额", d["os_cost_amt"])
        check_amount("应收金额", d["os_sell_amt"])
        validate_options(db, d)

    lines = []
    for d in (a, b):
        c = ChargeInfo(shipment_id=shipment.id, job_num=shipment.shipment_num,
                       operator=user.phone, **d)
        db.add(c)
        lines.append(c)
    db.flush()
    return lines


def update_line(db: Session, line: ChargeInfo, data: dict, user: User) -> ChargeInfo:
    """编辑费用信息：任务码不可改；重新执行金额与取值校验。"""
    for name, label in (("os_cost_amt", "应付金额"), ("os_sell_amt", "应收金额")):
        if name in data:
            check_amount(label, data[name])
    validate_options(db, data, existing=line)
    for k, v in data.items():
        setattr(line, k, v)
    line.operator = user.phone
    return line


def soft_delete(line: ChargeInfo, user: User) -> ChargeInfo:
    line.status = 1
    line.operator = user.phone
    return line
