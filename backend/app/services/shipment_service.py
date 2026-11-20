"""货运订单的业务规则：编号唯一性、状态流转矩阵。

路由只负责取数与判权限，规则集中在这里，便于独立测试。
"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Shipment, User
from app.repositories import shipment as shipment_repo

# 允许的业务状态流转（design D16）
TRANSITIONS = {
    ("draft", "confirmed"),
    ("draft", "cancelled"),
    ("confirmed", "completed"),
    ("confirmed", "cancelled"),
}


def normalize_number(raw: str) -> str:
    """去掉首尾空格；空值报 422。"""
    num = (raw or "").strip()
    if not num:
        raise HTTPException(status_code=422, detail="货运订单号必填")
    return num


def ensure_unique(db: Session, number: str, exclude_id: Optional[int] = None) -> None:
    """货运订单号全局唯一，比较不区分大小写；重复报 409。"""
    if shipment_repo.find_by_number(db, number, exclude_id):
        raise HTTPException(status_code=409, detail="该货运订单号已被使用")


def create_shipment(db: Session, number: str, user: User) -> Shipment:
    num = normalize_number(number)
    ensure_unique(db, num)
    s = Shipment(shipment_num=num, operator=user.phone)
    db.add(s)
    db.flush()
    return s


def update_shipment(db: Session, shipment: Shipment, number: str, user: User) -> Shipment:
    num = normalize_number(number)
    ensure_unique(db, num, exclude_id=shipment.id)
    shipment.shipment_num = num
    shipment.operator = user.phone
    return shipment


def soft_delete(shipment: Shipment, user: User) -> Shipment:
    shipment.status = 1
    shipment.operator = user.phone
    return shipment


def transition(db: Session, sid: int, target: str, user: User) -> Shipment:
    """单事务流转：行锁后校验矩阵，更新 lifecycle 与审计字段。"""
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
    return s
