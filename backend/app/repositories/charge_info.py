"""费用信息的查询助手：统一注入 `status = 0` 过滤。"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import ChargeInfo


def get_active(db: Session, line_id: int) -> Optional[ChargeInfo]:
    """取未删除的费用信息；不存在返回 None（由路由转成 404）。"""
    c = db.get(ChargeInfo, line_id)
    if not c or c.status != 0:
        return None
    return c


def lines_of(db: Session, shipment_id: int) -> List[ChargeInfo]:
    """某订单下全部未删除的费用信息，按录入顺序。"""
    return (
        db.query(ChargeInfo)
        .filter(ChargeInfo.shipment_id == shipment_id, ChargeInfo.status == 0)
        .order_by(ChargeInfo.id)
        .all()
    )
