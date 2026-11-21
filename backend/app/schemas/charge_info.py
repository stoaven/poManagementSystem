"""费用信息的请求体与响应体。

一条费用信息同时承载一笔应付与一笔应收（design D30）：
通用列 job_num / charge_code；
应付列 department / branch / cost_currency / os_cost_amt / creditor；
应收列 sell_currency / os_sell_amt / debtor。

金额在接口里一律以字符串传输，避免 JavaScript 的大数精度问题。
"""
from typing import Optional

from pydantic import BaseModel

from app.schemas.common import AuditOut


class ChargeInfoIn(BaseModel):
    """创建载荷：两侧必填。任务码由父订单带出，客户端传入即被忽略。"""

    charge_code: str
    department: str
    branch: str
    cost_currency: str
    os_cost_amt: str
    creditor: str
    sell_currency: str
    os_sell_amt: str
    debtor: str


class ChargeInfoPatch(BaseModel):
    """编辑载荷：字段全部可选（由服务层判断完整性）。"""

    charge_code: Optional[str] = None
    department: Optional[str] = None
    branch: Optional[str] = None
    cost_currency: Optional[str] = None
    os_cost_amt: Optional[str] = None
    creditor: Optional[str] = None
    sell_currency: Optional[str] = None
    os_sell_amt: Optional[str] = None
    debtor: Optional[str] = None


class ChargeInfoOut(AuditOut):
    """费用信息记录。"""

    id: int
    shipment_id: int
    job_num: str
    charge_code: str
    department: str
    branch: str
    cost_currency: Optional[str] = None
    os_cost_amt: Optional[str] = None
    creditor: Optional[str] = None
    sell_currency: Optional[str] = None
    os_sell_amt: Optional[str] = None
    debtor: Optional[str] = None


class ChargeInfoListOut(BaseModel):
    """新增费用信息后的响应：一次写入的两条记录。"""

    items: list[ChargeInfoOut] = []
