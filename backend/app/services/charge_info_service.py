"""费用信息的业务规则：成对写入、金额约束、分类字段取值校验。

**新增一条费用信息会写入两条记录**（design D30）：

页面填写的 10 个字段被拆到两条记录里——

| | A（应付侧那条） | B（镜像分支那条） |
|---|---|---|
| charge_code | 页面 | 页面 |
| description | 页面 | 页面 |
| department | 页面 | = A.department |
| branch | 页面 | 镜像分支（SHL↔SHO） |
| cost_currency | 页面 | = A.sell_currency |
| os_cost_amt | 页面 | = A.os_sell_amt |
| creditor | 页面 | 对家单位 |
| sell_currency | = A.cost_currency | 页面 |
| os_sell_amt | = A.os_cost_amt | 页面 |
| debtor | 对家单位 | 页面 |

「对家单位」按当前分支定：SHL 的对家是 CNSHO，SHO 的对家是 CNSHL。

**四个折算后金额按每条记录自己的币种算**（design D32）：
币种是本位币 CNY 时，估算成本 = 本地成本 = 该条的应付金额；
币种是本位币 CNY 时，估算收入 = 本地应收金额 = 该条的应收金额；
其余币种一律 0.00。
"""
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import ChargeCode, ChargeInfo, Shipment, User
from app.repositories.option import validate_option_value

MAX_AMT = Decimal("999999999999.99")

# 本位币：只有人民币才有折算后的估算/本地金额
LOCAL_CURRENCY = "CNY"

# 当前分支机构 -> 镜像分支
BRANCH_MIRROR = {"SHL": "SHO", "SHO": "SHL"}

# 当前分支机构 -> 对家单位。
# 每条记录的「对家」由它**自己所在的分支**决定：
# A 的应收对象看 A.branch，B 的应付对象看 B.branch。
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
        "description": c.description,
        "department": c.department,
        "branch": c.branch,
        "cost_currency": c.cost_currency,
        "os_cost_amt": money_text(c.os_cost_amt),
        "estimated_cost": money_text(c.estimated_cost),
        "local_cost_amt": money_text(c.local_cost_amt),
        "creditor": c.creditor,
        "sell_currency": c.sell_currency,
        "os_sell_amt": money_text(c.os_sell_amt),
        "estimated_revenue": money_text(c.estimated_revenue),
        "local_sell_amt": money_text(c.local_sell_amt),
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


def derive_amounts(record: dict) -> dict:
    """按记录**自己**的币种推出四个折算后金额。

    应付币种是本位币 CNY：估算成本 = 本地成本 = 该条的应付金额；否则都是 0.00。
    应收币种是本位币 CNY：估算收入 = 本地应收金额 = 该条的应收金额；否则都是 0.00。
    """
    zero = Decimal("0.00")
    cost = record.get("os_cost_amt")
    sell = record.get("os_sell_amt")
    cost_local = record.get("cost_currency") == LOCAL_CURRENCY
    sell_local = record.get("sell_currency") == LOCAL_CURRENCY
    cost_amt = Decimal(str(cost)) if cost is not None else zero
    sell_amt = Decimal(str(sell)) if sell is not None else zero
    return {
        "estimated_cost": cost_amt if cost_local else zero,
        "local_cost_amt": cost_amt if cost_local else zero,
        "estimated_revenue": sell_amt if sell_local else zero,
        "local_sell_amt": sell_amt if sell_local else zero,
    }


def resolve_description(db: Session, data: dict) -> Optional[str]:
    """描述取页面填的值；页面没填时，从费用代码表带出该 code 的描述。"""
    given = (data.get("description") or "").strip()
    if given:
        return given
    code = data.get("charge_code")
    if not code:
        return None
    row = db.query(ChargeCode).filter(ChargeCode.code == code).first()
    return row.description if row else None


def build_pair(data: dict, description: Optional[str] = None) -> Tuple[dict, dict]:
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
        "description": description,
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
    b_branch = BRANCH_MIRROR[branch]
    b = {
        "charge_code": a["charge_code"],
        "description": description,
        "department": a["department"],
        "branch": b_branch,
        "cost_currency": a["sell_currency"],
        "os_cost_amt": a["os_sell_amt"],
        # 对家单位按 B 自己的分支定：在 SHL 则对家 CNSHO，在 SHO 则 CNSHL
        "creditor": COUNTERPARTY[b_branch],
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
    description = resolve_description(db, data)
    a, b = build_pair(data, description)
    for d in (a, b):
        check_amount("应付金额", d["os_cost_amt"])
        check_amount("应收金额", d["os_sell_amt"])
        validate_options(db, d)
        # 四个折算后金额按各自的币种算
        d.update(derive_amounts(d))

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
    # 币种或金额改了，四个折算后金额要跟着按新币种重算
    for k, v in derive_amounts({
        "cost_currency": line.cost_currency,
        "os_cost_amt": line.os_cost_amt,
        "sell_currency": line.sell_currency,
        "os_sell_amt": line.os_sell_amt,
    }).items():
        setattr(line, k, v)
    line.operator = user.phone
    return line


def soft_delete(line: ChargeInfo, user: User) -> ChargeInfo:
    line.status = 1
    line.operator = user.phone
    return line
