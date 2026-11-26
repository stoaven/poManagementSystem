"""选项数据的批量导入：按 code upsert。

CSV 表头两列（列序不限、大小写不敏感）：`code` 与该类的标签列——
费用代码表是 `description`（描述），其余五类是 `name`（名称）：
- code 已存在 → 更新标签（code 不可改，这是选项表的一贯约束）
- code 不存在 → 新增
- code 对应的选项**已被软删除** → 跳过并报告，不复活——删除是有人刻意做的，
  批量导入不该悄悄推翻它
"""
import csv
import io
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import User
from app.repositories.option import MODEL_BY_KIND, label_column

MAX_CODE_LEN = 64
MAX_NAME_LEN = 200
# 报告里最多列多少条明细，再多就只给个数
MAX_REPORTED = 20


def _model(kind: str):
    m = MODEL_BY_KIND.get(kind)
    if not m:
        raise HTTPException(status_code=404, detail="无效的选项类别")
    return m


def parse_csv(kind: str, content: bytes):
    """解析 CSV，返回 (代码, 标签) 的列表；表头不对就报错。"""
    # utf-8-sig：Excel 导出的 CSV 开头带 BOM，不剥掉的话第一个表头会变成 "﻿code"
    text = content.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise HTTPException(status_code=422, detail="文件是空的")

    label_col = label_column(_model(kind))
    header = [h.strip().lower() for h in rows[0]]
    if "code" not in header or label_col not in header:
        raise HTTPException(
            status_code=422,
            detail=f"表头必须是 code 和 {label_col} 两列（第一行）",
        )
    ci = header.index("code")
    ni = header.index(label_col)

    items = []
    for row in rows[1:]:
        if not row or all(not c.strip() for c in row):
            continue  # 空行
        code = row[ci].strip() if ci < len(row) else ""
        label = row[ni].strip() if ni < len(row) else ""
        items.append((code, label))
    return items


def import_options(db: Session, kind: str, content: bytes,
                    admin: User) -> dict:
    """按 code upsert 一批选项项，返回统计。"""
    m = _model(kind)
    label_col = label_column(m)
    items = parse_csv(kind, content)

    created = 0
    updated = 0
    skipped: List[str] = []
    errors: List[str] = []

    for idx, (code, label) in enumerate(items, start=2):
        if not code:
            errors.append(f"第 {idx} 行没有 code")
            continue
        if len(code) > MAX_CODE_LEN:
            errors.append(f"第 {idx} 行 code 超过 {MAX_CODE_LEN} 个字符")
            continue
        if len(label) > MAX_NAME_LEN:
            errors.append(f"第 {idx} 行 {label_col} 超过 {MAX_NAME_LEN} 个字符")
            continue

        existing = db.query(m).filter(m.code == code).first()
        if existing is None:
            o = m(code=code, is_active=True, status=0, operator=admin.phone)
            setattr(o, label_col, label or None)
            db.add(o)
            created += 1
            continue
        if existing.status == 1:
            skipped.append(code)   # 已删除的项不复活
            continue
        setattr(existing, label_col, label or None)
        existing.operator = admin.phone
        updated += 1

    db.flush()
    return {
        "created": created,
        "updated": updated,
        "skipped": len(skipped),
        "skipped_codes": skipped[:MAX_REPORTED],
        "errors": errors[:MAX_REPORTED],
        "total": len(items),
    }


def import_summary(result: dict) -> str:
    """给界面的一句话说明。"""
    parts = [f"新增 {result['created']} 条", f"更新 {result['updated']} 条"]
    if result["skipped"]:
        parts.append(f"跳过 {result['skipped']} 条（已删除的 code）")
    if result["errors"]:
        parts.append(f"{len(result['errors'])} 行有问题")
    return "导入完成：" + "，".join(parts)
