"""货运订单的查询助手。

统一在这里注入 `status = 0` 过滤（软删除的订单一律不可见）、集中定义筛选
条件与聚合查询——路由层不再各自拼查询，避免「漏加过滤条件」这类问题。
"""
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ChargeInfo, Shipment


def get_active(db: Session, sid: int) -> Optional[Shipment]:
    """取未删除的订单；不存在返回 None（由路由转成 404）。"""
    s = db.get(Shipment, sid)
    if not s or s.status != 0:
        return None
    return s


def query_active(db: Session, keyword: str = "", lifecycle: str = ""):
    """列表查询：货运订单号关键字（模糊、不区分大小写）+ 业务状态。"""
    q = db.query(Shipment).filter(Shipment.status == 0)
    if keyword:
        kw = keyword.strip().lower()
        # MySQL utf8mb4_0900_ai_ci 本就大小写不敏感；lower() 保证与预检语义一致
        q = q.filter(func.lower(Shipment.shipment_num).contains(kw))
    if lifecycle:
        q = q.filter(Shipment.lifecycle == lifecycle)
    return q


def find_by_number(db: Session, number: str, exclude_id: Optional[int] = None):
    """按货运订单号找订单，比较不区分大小写、不忽略首尾空格以外的形式。"""
    q = db.query(Shipment).filter(func.lower(Shipment.shipment_num) == number.lower())
    if exclude_id is not None:
        q = q.filter(Shipment.id != exclude_id)
    return q.first()


def paged(db: Session, keyword: str = "", lifecycle: str = "",
          page: int = 1, page_size: int = 20):
    """分页取订单：默认按创建时间倒序，返回 (总数, 当前页的订单)。"""
    q = query_active(db, keyword, lifecycle)
    total = q.count()
    items = (
        q.order_by(Shipment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return total, items


def line_counts(db: Session, ids: List[int]) -> Dict[int, int]:
    """一次分组查询拿到每个订单下的费用信息条数。"""
    if not ids:
        return {}
    rows = (
        db.query(ChargeInfo.shipment_id, func.count(ChargeInfo.id))
        .filter(ChargeInfo.shipment_id.in_(ids), ChargeInfo.status == 0)
        .group_by(ChargeInfo.shipment_id)
        .all()
    )
    return dict(rows)
