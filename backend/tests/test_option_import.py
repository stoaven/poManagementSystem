"""批量导入：按 code upsert。"""
import io

from app.models import ChargeCode, Department

KINDS = ["charge_codes", "departments", "branches", "currencies",
         "creditors", "debtors"]


def test_import_creates_and_updates(client, admin_headers, seeded_options):
    """已存在的 code 更新名称，不存在的 code 新增。"""
    r = client.post("/api/v1/options/charge_codes/import",
                    headers=admin_headers,
                    files={"file": ("o.csv", io.BytesIO(
                        "code,name\nDHLF,快递国际\nOCUC,海洋附加费\nNEWC,新代码\n"
                        .encode("utf-8")), "text/csv")})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["created"] == 1      # NEWC 是新的
    assert body["updated"] == 2      # DHLF、OCUC 原来就有
    assert body["skipped"] == 0
    assert body["total"] == 3

    items = client.get("/api/v1/options/charge_codes",
                       headers=admin_headers).json()["items"]
    dhlf = next(o for o in items if o["code"] == "DHLF")
    assert dhlf["name"] == "快递国际"       # 名称被更新
    assert any(o["code"] == "NEWC" for o in items)  # 新增


def test_import_skips_deleted_code(client, admin_headers, db, seeded_options):
    """已软删除的 code 不复活，跳过并报告。"""
    c = db.query(ChargeCode).filter_by(code="DHLF").first()
    assert client.delete(f"/api/v1/options/charge_codes/{c.id}",
                         headers=admin_headers).status_code == 200

    r = client.post("/api/v1/options/charge_codes/import",
                    headers=admin_headers,
                    files={"file": ("o.csv", io.BytesIO(
                        "code,name\nDHLF,快递国际\nOCUC,海洋附加费\n"
                        .encode("utf-8")), "text/csv")})
    assert r.status_code == 200
    body = r.json()
    assert body["updated"] == 1        # OCUC 被更新
    assert body["skipped"] == 1        # DHLF 被跳过
    assert body["skipped_codes"] == ["DHLF"]

    # 被跳过的那个仍然是已删除状态
    items = client.get("/api/v1/options/charge_codes", headers=admin_headers,
                       params={"include_deleted": True}).json()["items"]
    dhlf = next(o for o in items if o["code"] == "DHLF")
    assert dhlf["deleted"] is True


def test_import_rejects_bad_header(client, admin_headers, seeded_options):
    r = client.post("/api/v1/options/departments/import",
                    headers=admin_headers,
                    files={"file": ("o.csv", io.BytesIO(
                        "部门,名称\nFIS,应付部门\n".encode("utf-8")), "text/csv")})
    assert r.status_code == 422
    assert "code" in r.json()["detail"]


def test_import_reports_rows_without_code(client, admin_headers, seeded_options):
    r = client.post("/api/v1/options/departments/import",
                    headers=admin_headers,
                    files={"file": ("o.csv", io.BytesIO(
                        "code,name\nFIS,应付部门\n,没有代码\n".encode("utf-8")),
                        "text/csv")})
    assert r.status_code == 200
    body = r.json()
    assert body["created"] == 0
    assert body["updated"] == 1
    assert body["errors"]            # 有一行报错了


def test_import_handles_bom_and_crlf(client, admin_headers, seeded_options):
    """Excel 导出的 CSV 带 BOM 且用 CRLF 换行，都要能读。"""
    raw = "﻿code,name\r\nFIS2,应付部门\r\n".encode("utf-8")
    r = client.post("/api/v1/options/departments/import",
                    headers=admin_headers,
                    files={"file": ("o.csv", io.BytesIO(raw), "text/csv")})
    assert r.status_code == 200, r.text
    assert r.json()["created"] == 1
    assert db_has_department("FIS2", client, admin_headers)


def db_has_department(code, client, admin_headers):
    items = client.get("/api/v1/options/departments",
                       headers=admin_headers).json()["items"]
    return any(o["code"] == code for o in items)


def test_import_works_for_all_six_kinds(client, admin_headers, seeded_options):
    """六类选项都能批量导入。"""
    for i, kind in enumerate(KINDS):
        r = client.post(f"/api/v1/options/{kind}/import",
                        headers=admin_headers,
                        files={"file": ("o.csv", io.BytesIO(
                            f"code,name\nIMP{i},批量导入{i}\n".encode("utf-8")),
                            "text/csv")})
        assert r.status_code == 200, (kind, r.text)
        assert r.json()["created"] == 1, kind


def test_import_unknown_kind_is_404(client, admin_headers, seeded_options):
    r = client.post("/api/v1/options/nope/import", headers=admin_headers,
                    files={"file": ("o.csv", io.BytesIO(
                        "code,name\nA,B\n".encode("utf-8")), "text/csv")})
    assert r.status_code == 404


def test_import_normal_user_forbidden(client, normal_headers, seeded_options):
    r = client.post("/api/v1/options/charge_codes/import", headers=normal_headers,
                    files={"file": ("o.csv", io.BytesIO(
                        "code,name\nA,B\n".encode("utf-8")), "text/csv")})
    assert r.status_code == 403
