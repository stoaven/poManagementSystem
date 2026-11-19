"""选项仓储：字段标识到选项表的映射与三态校验（design D13）。

校验三态：
- 取值不存在 -> 拒绝（无效）
- 取值已停用 -> 新建拒绝；编辑保留原值通过；编辑改为该值拒绝
- 取值已删除 -> 拒绝（已被删除）
"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    BranchOption,
    ChargeCode,
    Creditor,
    Currency,
    Debtor,
    Department,
)

# 分类字段标识 -> 选项模型
FIELD_MODEL_MAP = {
    "charge_codes": ChargeCode,
    "departments": Department,
    "branches": BranchOption,
    "currencies": Currency,
    "creditors": Creditor,
    "debtors": Debtor,
}


def validate_option_value(db: Session, kind: str, value: str,
                          editing: bool = False, unchanged: bool = False):
    """校验某分类字段的取值。editing=True 表示处于编辑流程，unchanged 表示取值未变。"""
    m = FIELD_MODEL_MAP.get(kind)
    if not m:
        raise HTTPException(status_code=422, detail=f"未知的选项类别 {kind}")
    o = db.query(m).filter(m.code == value).first()
    if not o:
        raise HTTPException(status_code=422, detail=f"取值 {value} 无效")
    if o.status != 0:
        raise HTTPException(status_code=422, detail=f"取值 {value} 已被删除")
    if not o.is_active:
        if editing and unchanged:
            return  # 编辑保留已停用的原值：通过
        raise HTTPException(status_code=422, detail=f"取值 {value} 已停用")
