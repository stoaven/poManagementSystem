"""货运订单路由：CRUD + 状态流转 + 详情按币种合计。

筛选只提供 shipment_num 关键字与业务状态；不提供金额区间（spec）。
路由只做取数与判权限，规则在 `app/services/shipment_service.py`，
查询助手在 `app/repositories/shipment.py`。
"""
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.repositories import charge_info as charge_info_repo
from app.repositories import shipment as shipment_repo
from app.schemas.common import OkOut
from app.schemas.shipments import (
    ShipmentBrief,
    ShipmentDetailOut,
    ShipmentIn,
    ShipmentListOut,
)
from app.services import charge_info_service as charge_info_svc
from app.services import export_service
from app.services import shipment_service as svc

router = APIRouter(prefix="/shipments", tags=["shipments"])


def _get_or_404(db: Session, sid: int):
    s = shipment_repo.get_active(db, sid)
    if not s:
        raise HTTPException(status_code=404, detail="该货运订单不存在")
    return s


def _brief(s) -> dict:
    return {"id": s.id, "shipment_num": s.shipment_num, "lifecycle": s.lifecycle,
            "operator": s.operator}


@router.get("", response_model=ShipmentListOut)
def list_shipments(
    keyword: str = "",
    lifecycle: str = "",
    page: int = 1,
    page_size: int = 20,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total, items = shipment_repo.paged(db, keyword, lifecycle, page, page_size)
    counts = shipment_repo.line_counts(db, [s.id for s in items])
    return {
        "items": [
            {
                "id": s.id,
                "shipment_num": s.shipment_num,
                "lifecycle": s.lifecycle,
                "status": s.status,
                "operator": s.operator,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                "charge_info_count": counts.get(s.id, 0),
            }
            for s in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", status_code=201, response_model=ShipmentBrief)
def create_shipment(body: ShipmentIn, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    return _brief(svc.create_shipment(db, body.shipment_num, user))


@router.patch("/{sid}", response_model=ShipmentBrief)
def update_shipment(sid: int, body: ShipmentIn, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    s = _get_or_404(db, sid)
    return _brief(svc.update_shipment(db, s, body.shipment_num, user))


@router.delete("/{sid}", response_model=OkOut)
def delete_shipment(sid: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    s = _get_or_404(db, sid)
    svc.soft_delete(s, user)
    return {"ok": True}


@router.get("/{sid}", response_model=ShipmentDetailOut)
def get_shipment(sid: int, _: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    s = _get_or_404(db, sid)
    lines = charge_info_repo.lines_of(db, s.id)
    return {
        "id": s.id,
        "shipment_num": s.shipment_num,
        "lifecycle": s.lifecycle,
        "status": s.status,
        "operator": s.operator,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        "charge_info": [charge_info_svc.line_to_dict(c) for c in lines],
    }


@router.get("/{sid}/charge-infos/export")
def export_charge_infos(sid: int, _: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """把该货运订单下的全部费用信息导出为 Excel（英文表头）。"""
    s = _get_or_404(db, sid)
    lines = charge_info_repo.lines_of(db, s.id)
    content = export_service.build_charge_info_workbook(lines)
    filename = export_service.export_filename(s.shipment_num)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument."
                   "spreadsheetml.sheet",
        headers={
            "Content-Disposition": (
                f"attachment; filename=\"{filename}\"; "
                f"filename*=UTF-8''{quote(filename)}"
            )
        },
    )


@router.post("/{sid}/confirm", response_model=ShipmentBrief)
def confirm_shipment(sid: int, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    return _brief(svc.transition(db, sid, "confirmed", user))


@router.post("/{sid}/complete", response_model=ShipmentBrief)
def complete_shipment(sid: int, user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    return _brief(svc.transition(db, sid, "completed", user))


@router.post("/{sid}/cancel", response_model=ShipmentBrief)
def cancel_shipment(sid: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    return _brief(svc.transition(db, sid, "cancelled", user))
