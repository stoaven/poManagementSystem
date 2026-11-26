"""六类选项的批量导入，逐类验证正确性。

每类都要确认三件事：
- 新 code 落到**这一类**的表里
- 已存在的 code 更新的是**这一类**的表里的那一条
- 已软删除的 code 被跳过、不会被复活
另外确认导入不会串到别的表去。
"""
import io

import pytest

from app.models import (
    BranchOption,
    ChargeCode,
    Creditor,
    Currency,
    Debtor,
    Department,
)
from app.repositories.option import label_column

# 每类：选项模型、该类里已有的一个 code、该类里已有的一个名称
KINDS = [
    ("charge_codes", ChargeCode, "DHLF"),
    ("departments", Department, "FIS"),
    ("branches", BranchOption, "SHL"),
    ("currencies", Currency, "USD"),
    ("creditors", Creditor, "CNSHL"),
    ("debtors", Debtor, "CNSHO"),
]

ALL_MODELS = [m for _, m, _ in KINDS]


def _post(client, headers, kind, csv_text):
    r = client.post(
        f"/api/v1/options/{kind}/import",
        headers=headers,
        files={"file": ("o.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")},
    )
    return r


@pytest.mark.parametrize("kind,model,existing_code", KINDS)
def test_import_into_each_kind(client, admin_headers, db, seeded_options,
                               kind, model, existing_code):
    """逐类导入：新增、更新、跳过，三条路径都要落到正确的表。"""
    new_code = f"IMP_{kind.upper()[:3]}"

    # 1) 导入一个没见过的 code + 一个已存在的 code
    label_col = label_column(model)
    csv_text = (f"code,{label_col}\n{new_code},批量导入的名称\n"
                f"{existing_code},改过的名称\n")
    r = _post(client, admin_headers, kind, csv_text)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["created"] == 1, (kind, body)
    assert body["updated"] == 1, (kind, body)
    assert body["skipped"] == 0, (kind, body)

    # 2) 新增的那条在**这一类**的表里，名称就是 CSV 里的
    row = db.query(model).filter(model.code == new_code).first()
    assert row is not None, f"{kind} 的表里没有 {new_code}"
    assert getattr(row, label_col) == "批量导入的名称"
    assert row.status == 0
    assert row.is_active is True

    # 3) 已存在的那条名称被更新了
    old = db.query(model).filter(model.code == existing_code).first()
    assert getattr(old, label_col) == "改过的名称"

    # 4) 没有串到别的表去
    for other in ALL_MODELS:
        if other is model:
            continue
        assert db.query(other).filter(other.code == new_code).first() is None, \
            f"{new_code} 串到了别的表"


@pytest.mark.parametrize("kind,model,existing_code", KINDS)
def test_import_skips_deleted_in_each_kind(client, admin_headers, db,
                                           seeded_options, kind, model,
                                           existing_code):
    """逐类：已软删除的 code 被跳过，不复活。"""
    row = db.query(model).filter(model.code == existing_code).first()
    assert client.delete(f"/api/v1/options/{kind}/{row.id}",
                         headers=admin_headers).status_code == 200

    label_col = label_column(model)
    r = _post(client, admin_headers, kind,
              f"code,{label_col}\n{existing_code},想把它带回来\n")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["skipped"] == 1, (kind, body)
    assert body["created"] == 0
    assert body["updated"] == 0
    assert body["skipped_codes"] == [existing_code]

    db.expire_all()
    still = db.query(model).filter(model.code == existing_code).first()
    assert still.status == 1, "已删除的项被复活了"
    assert getattr(still, label_col) != "想把它带回来"


@pytest.mark.parametrize("kind,model,existing_code", KINDS)
def test_import_visible_in_that_kind_only(client, admin_headers, db,
                                          seeded_options, kind, model,
                                          existing_code):
    """逐类：导入的项出现在该类的管理列表与候选列表里。"""
    new_code = f"VIS_{kind.upper()[:3]}"
    label_col = label_column(model)
    r = _post(client, admin_headers, kind, f"code,{label_col}\n{new_code},可见性\n")
    assert r.status_code == 200, r.text

    admin_items = client.get(f"/api/v1/options/{kind}",
                             headers=admin_headers).json()["items"]
    assert any(o["code"] == new_code for o in admin_items)

    cand = client.get(f"/api/v1/options/{kind}/options",
                      headers=admin_headers).json()["items"]
    assert any(o["code"] == new_code for o in cand)


def test_import_rejects_bad_header_for_every_kind(client, admin_headers,
                                                  seeded_options):
    """逐类：表头不对都要被拒绝。"""
    for kind, model, _code in KINDS:
        # 用「另一列」当表头：对 charge_codes 来说 name 是错的那一列
        wrong = "name" if label_column(model) == "description" else "description"
        r = _post(client, admin_headers, kind, f"code,{wrong}\nA,B\n")
        assert r.status_code == 422, (kind, r.status_code)
        assert "code" in r.json()["detail"]


def test_import_empty_file_for_every_kind(client, admin_headers,
                                          seeded_options):
    """逐类：空文件被拒绝。"""
    for kind, _model, _code in KINDS:
        r = _post(client, admin_headers, kind, "")
        assert r.status_code == 422, (kind, r.status_code)
