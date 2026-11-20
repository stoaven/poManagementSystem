"""费用信息的业务规则：金额约束、分类字段取值校验、关联生成。

关联生成（design D11）：
- 源 Branch=SHL 且 Debtor=CNSHO -> 关联记录 Branch=SHO、Creditor=CNSHL、
  应付币种/金额取源记录的应收侧
- 源 Branch=SHO 且 Creditor=CNSHL -> 关联记录 Branch=SHL、Debtor=CNSHO、
  应收币种/金额取源记录的应付侧
- 费用代码与应付部门复制源记录；未填写的一侧留空
- 关联记录（related_source_id 非空）不能再生成关联记录
"""
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import ChargeInfo, Shipment, User
from app.repositories.option import validate_option_value

MAX_AMT = Decimal("999999999999.99")

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

# 两条对称的生成规则：源记录的 (分支机构, 对象) -> 关联记录的对应取值
RELATED_RULES = {
    ("SHL", "CNSHO"): {"branch": "SHO", "creditor": "CNSHL"},
    ("SHO", "CNSHL"): {"branch": "SHL", "debtor": "CNSHO"},
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
        "related_source_id": c.related_source_id,
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


def create_line(db: Session, shipment: Shipment, data: dict, user: User) -> ChargeInfo:
    """新增费用信息：任务码由所属订单带出，客户端传入即被忽略。

    带 related_source_id 的是「添加关联费用」——用户在弹窗里确认过才落库，
    这里再校验一次源记录，避免链式生成。
    """
    related_source_id = data.pop("related_source_id", None)
    if related_source_id is not None:
        check_related_source(db, shipment, related_source_id)
    check_amount("应付金额", data["os_cost_amt"])
    check_amount("应收金额", data["os_sell_amt"])
    validate_options(db, data)
    c = ChargeInfo(shipment_id=shipment.id, job_num=shipment.shipment_num,
                   related_source_id=related_source_id,
                   operator=user.phone, **data)
    db.add(c)
    db.flush()
    return c


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


def related_draft(source: ChargeInfo) -> dict:
    """由源记录算出关联费用信息的取值——**只算不落库**。

    用户在弹窗里看到这些预填值，补齐未填写的一侧后点确定，才真正写入。
    关联记录本身不再生成关联记录，否则会链式生成下去。
    """
    if source.related_source_id is not None:
        raise HTTPException(status_code=409, detail="关联生成的记录不能再生成关联记录")

    rule = RELATED_RULES.get((source.branch, source.debtor))
    if rule:
        return {
            "related_source_id": source.id,
            "charge_code": source.charge_code,
            "department": source.department,
            "branch": rule["branch"],
            "creditor": rule["creditor"],
            "cost_currency": source.sell_currency,
            "os_cost_amt": money_text(source.os_sell_amt),
            "sell_currency": None,
            "os_sell_amt": None,
            "debtor": None,
        }
    if (source.branch, source.creditor) == ("SHO", "CNSHL"):
        return {
            "related_source_id": source.id,
            "charge_code": source.charge_code,
            "department": source.department,
            "branch": "SHL",
            "creditor": None,
            "cost_currency": None,
            "os_cost_amt": None,
            "sell_currency": source.cost_currency,
            "os_sell_amt": money_text(source.os_cost_amt),
            "debtor": "CNSHO",
        }
    raise HTTPException(status_code=409, detail="该记录不满足关联生成条件")


def check_related_source(db: Session, shipment: Shipment,
                         related_source_id: int) -> ChargeInfo:
    """校验关联费用的源记录：存在、未删除、不是关联记录、属于同一订单。"""
    src = db.get(ChargeInfo, related_source_id)
    if not src or src.status != 0:
        raise HTTPException(status_code=404, detail="源费用信息不存在")
    if src.related_source_id is not None:
        raise HTTPException(status_code=409, detail="关联生成的记录不能再生成关联记录")
    if src.shipment_id != shipment.id:
        raise HTTPException(status_code=422, detail="源费用信息不属于该货运订单")
    return src
