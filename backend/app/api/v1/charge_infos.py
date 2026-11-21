"""费用信息路由：创建 / 编辑 / 软删除 / 关联生成。

路由只做取数与判权限，业务规则在 `app/services/charge_info_service.py`，
查询助手在 `app/repositories/charge_info.py`。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.repositories import charge_info as charge_info_repo
from app.repositories import shipment as shipment_repo
from app.schemas.charge_info import (
    ChargeInfoIn,
    ChargeInfoOut,
    ChargeInfoPatch,
)
from app.schemas.common import OkOut
from app.services import charge_info_service as svc

router = APIRouter(tags=["charge-info"])


def _get_line_or_404(db: Session, line_id: int):
    c = charge_info_repo.get_active(db, line_id)
    if not c:
        raise HTTPException(status_code=404, detail="该费用信息不存在")
    return c


@router.post("/shipments/{sid}/charge-infos", status_code=201,
             response_model=ChargeInfoOut)
def create_charge_info(sid: int, body: ChargeInfoIn,
                       user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    s = shipment_repo.get_active(db, sid)
    if not s:
        raise HTTPException(status_code=404, detail="该货运订单不存在")
    c = svc.create_line(db, s, body.model_dump(), user)
    return svc.line_to_dict(c)


@router.patch("/charge-infos/{line_id}", response_model=ChargeInfoOut)
def update_charge_info(line_id: int, body: ChargeInfoPatch,
                       user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    c = _get_line_or_404(db, line_id)
    updated = svc.update_line(db, c, body.model_dump(exclude_none=True), user)
    return svc.line_to_dict(updated)


@router.delete("/charge-infos/{line_id}", response_model=OkOut)
def delete_charge_info(line_id: int, user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    c = _get_line_or_404(db, line_id)
    svc.soft_delete(c, user)
    return {"ok": True}
