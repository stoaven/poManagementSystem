"""货运订单的请求体与响应体。"""
from pydantic import BaseModel

from app.schemas.charge_info import ChargeInfoOut
from app.schemas.common import AuditOut


class ShipmentIn(BaseModel):
    """新建与修改货运订单：只有货运订单号一个业务字段。"""

    shipment_num: str


class ShipmentBrief(BaseModel):
    """创建、修改与状态流转的响应。"""

    id: int
    shipment_num: str
    lifecycle: str
    operator: str


class ShipmentListItem(AuditOut):
    """列表中的每一行：只给定位所需的信息，不含任何金额。"""

    id: int
    shipment_num: str
    lifecycle: str
    charge_info_count: int = 0


class ShipmentListOut(BaseModel):
    items: list[ShipmentListItem]
    total: int
    page: int
    page_size: int


class ShipmentDetailOut(AuditOut):
    """订单详情：含其下全部未删除的费用信息。

    不做金额合计——合计带已从界面上移除，聚合查询随之取消。
    """

    id: int
    shipment_num: str
    lifecycle: str
    charge_info: list[ChargeInfoOut] = []
