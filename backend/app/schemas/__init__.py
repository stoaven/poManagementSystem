"""请求体与响应体模型。

路由层只做取数与业务判断，接口形状由这里的 Pydantic 模型描述；
OpenAPI 契约因此同时覆盖请求与响应。
"""
from app.schemas.auth import LoginIn, LoginOut, MeOut, UserBrief
from app.schemas.charge_info import (
    ChargeInfoIn,
    ChargeInfoOut,
    ChargeInfoPatch,
)
from app.schemas.common import AuditOut, OkOut
from app.schemas.options import (
    OptionCandidatesOut,
    OptionDeleteOut,
    OptionIn,
    OptionListOut,
    OptionOut,
    OptionStatusIn,
    ReferencesOut,
)
from app.schemas.shipments import (
    ShipmentBrief,
    ShipmentDetailOut,
    ShipmentIn,
    ShipmentListItem,
    ShipmentListOut,
)
from app.schemas.users import AuthorityPatch, StatusIn, UserIn, UserListOut, UserOut

__all__ = [
    "AuditOut",
    "AuthorityPatch",
    "ChargeInfoIn",
    "ChargeInfoOut",
    "ChargeInfoPatch",
    "LoginIn",
    "LoginOut",
    "MeOut",
    "OkOut",
    "OptionCandidatesOut",
    "OptionDeleteOut",
    "OptionIn",
    "OptionListOut",
    "OptionOut",
    "OptionStatusIn",
    "ReferencesOut",
    "ShipmentBrief",
    "ShipmentDetailOut",
    "ShipmentIn",
    "ShipmentListItem",
    "ShipmentListOut",
    "StatusIn",
    "UserBrief",
    "UserIn",
    "UserListOut",
    "UserOut",
]
