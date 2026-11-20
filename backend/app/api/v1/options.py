"""选项路由：六类共用一套端点，按 kind 分发。

路由只做取数与判权限，业务规则在 `app/services/option_service.py`，
取值校验与类别映射在 `app/repositories/option.py`。

candidates 必须注册在 /{kind} 之前，否则会被当成一个 kind 匹配掉（design D21）。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import User
from app.repositories.option import MODEL_BY_KIND
from app.schemas.options import (
    OptionCandidatesOut,
    OptionDeleteOut,
    OptionIn,
    OptionListOut,
    OptionOut,
    OptionStatusIn,
    ReferencesOut,
)
from app.services import option_service as svc

router = APIRouter(prefix="/options", tags=["options"])


def _resolve(kind: str):
    m = MODEL_BY_KIND.get(kind)
    if not m:
        raise HTTPException(status_code=404, detail="无效的选项类别")
    return m


@router.get("/candidates", response_model=OptionCandidatesOut)
def candidates(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """一次取回六类候选（启用且未删除）。"""
    result = {}
    for kind in MODEL_BY_KIND:
        result[kind] = svc.candidate_list(db, kind)
    return {"kinds": result}


@router.get("/{kind}", response_model=OptionListOut)
def admin_list(kind: str, include_deleted: bool = False,
               _: User = Depends(require_admin), db: Session = Depends(get_db)):
    """管理列表（admin-only）。include_deleted=True 时包含已删除项。

    每一项附带被引用它未删除费用信息条数，供界面上直接显示。
    """
    _resolve(kind)
    return {"items": svc.admin_list(db, kind, include_deleted)}


@router.get("/{kind}/options", response_model=OptionListOut)
def candidate_list(kind: str, q: str = "", _: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    """候选列表（登录即可读），支持按 code/name 关键字过滤。"""
    _resolve(kind)
    return {"items": svc.candidate_list(db, kind, q)}


@router.post("/{kind}", status_code=201, response_model=OptionOut)
def create_option(kind: str, body: OptionIn, admin: User = Depends(require_admin),
                  db: Session = Depends(get_db)):
    return svc.create(db, kind, body.code, body.name, admin)


@router.patch("/{kind}/{option_id}", response_model=OptionOut)
def update_option(kind: str, option_id: int, body: OptionIn,
                  admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """编辑：只允许改名称；code 一经创建不可修改。"""
    return svc.update(db, kind, option_id, body.code, body.name, admin)


@router.patch("/{kind}/{option_id}/status", response_model=OptionOut)
def set_option_status(kind: str, option_id: int, body: OptionStatusIn,
                      admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """启用/停用。停用项不出现在候选列表，但仍可被费用信息引用。"""
    return svc.set_active(db, kind, option_id, body.is_active, admin)


@router.get("/{kind}/{option_id}/references", response_model=ReferencesOut)
def option_references(kind: str, option_id: int, _: User = Depends(require_admin),
                       db: Session = Depends(get_db)):
    """删除前的引用数量预检（spec：删除前告知引用条数）。"""
    m = _resolve(kind)
    o = db.get(m, option_id)
    if not o or o.status != 0:
        raise HTTPException(status_code=404, detail="该选项不存在")
    return {"referenced": svc.reference_count(db, kind, o.code)}


@router.delete("/{kind}/{option_id}", response_model=OptionDeleteOut)
def delete_option(kind: str, option_id: int, admin: User = Depends(require_admin),
                  db: Session = Depends(get_db)):
    """软删除：status 置 1，返回删除前的引用数量。"""
    return svc.soft_delete(db, kind, option_id, admin)
