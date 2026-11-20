"""选项表的请求体与响应体（六类共用同一套形状）。"""
from typing import Optional

from pydantic import BaseModel

from app.schemas.common import AuditOut


class OptionIn(BaseModel):
    """新建选项的载荷：code 唯一且创建后不可修改，名称可省略。"""

    code: str
    name: Optional[str] = None


class OptionStatusIn(BaseModel):
    """启用/停用。"""

    is_active: bool


class OptionOut(AuditOut):
    """一个选项项。

    referenced 是引用它的未删除费用信息条数，管理列表据此提示删除影响。
    """

    id: int
    code: str
    name: str
    is_active: bool
    deleted: bool
    referenced: int = 0


class OptionListOut(BaseModel):
    items: list[OptionOut]


class OptionCandidatesOut(BaseModel):
    """一次取回六类候选：键为类别标识，值为该类的候选项。"""

    kinds: dict[str, list[OptionOut]]


class ReferencesOut(BaseModel):
    """删除前的引用数量预检。"""

    referenced: int


class OptionDeleteOut(BaseModel):
    """删除选项的响应：同时返回删除前的引用数量。"""

    ok: bool
    referenced: int
