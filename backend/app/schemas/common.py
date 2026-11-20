"""通用响应模型。

各能力的请求体与响应体都放在 schemas 包里，路由只负责取数与业务判断，
接口的形状由 Pydantic 模型描述——OpenAPI 契约因此能完整描述请求与响应，
前端可以据此生成 TypeScript 类型而不必手写（design D1/D19）。
"""
from typing import Optional

from pydantic import BaseModel


class OkOut(BaseModel):
    """通用成功响应。"""

    ok: bool


class AuditOut(BaseModel):
    """审计四件套：操作人、创建时间、更新时间、软删除标记。"""

    status: int = 0
    operator: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
