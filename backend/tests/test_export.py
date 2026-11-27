"""导出的 CSV：英文表头、内容、金额写法与文件类型。"""
import csv
import io


def _load(content: bytes):
    """读回 CSV：按 utf-8-sig 解（文件带 BOM），再按 CSV 规则拆行。"""
    text = content.decode("utf-8-sig")
    return list(csv.reader(io.StringIO(text)))


def test_export_returns_csv_with_english_headers(client, admin_headers,
                                                  seeded_shipment, seeded_charge):
    r = client.get(f"/api/v1/shipments/{seeded_shipment.id}/charge-infos/export",
                   headers=admin_headers)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/csv")
    assert "charge-info" in r.headers["content-disposition"]
    assert "attachment" in r.headers["content-disposition"]
    assert ".csv" in r.headers["content-disposition"]

    rows = _load(r.content)
    assert rows[0] == [
        "Charge Code", "Description", "Department", "Branch",
        "Cost Currency", "Estimated Cost", "OS Cost Amt",
        "Local Cost Amt", "Creditor", "Sell Currency", "OS Sell Amt",
        "Estimated Revenue", "Local Sell Amt", "Debtor",
    ]


def test_export_has_utf8_bom_for_excel(client, admin_headers,
                                        seeded_shipment, seeded_charge):
    """带 BOM：Excel 双击打开时中文不乱码。"""
    r = client.get(f"/api/v1/shipments/{seeded_shipment.id}/charge-infos/export",
                   headers=admin_headers)
    assert r.content.startswith(b"\xef\xbb\xbf")


def test_export_rows_match_charge_info(client, admin_headers, db, admin_user,
                                        seeded_shipment, seeded_charge):
    from app.models import ChargeInfo

    db.add(ChargeInfo(
        shipment_id=seeded_shipment.id, job_num=seeded_shipment.shipment_num,
        charge_code="OCUC", description="清关费",
        department="FIS", branch="SHO",
        cost_currency="CNY", os_cost_amt=2280, creditor="CNSHL",
        sell_currency="USD", os_sell_amt=8600, debtor="CNSHO",
        estimated_cost=2280, local_cost_amt=2280,
        estimated_revenue=0, local_sell_amt=0,
        status=0, operator=admin_user.phone))
    db.flush()

    r = client.get(f"/api/v1/shipments/{seeded_shipment.id}/charge-infos/export",
                   headers=admin_headers)
    assert r.status_code == 200
    rows = _load(r.content)
    assert len(rows) == 3      # 表头 + 两条记录

    first = rows[1]
    assert first[0] == "DHLF"          # Charge Code
    assert first[1] == "快递国际"       # Description
    assert first[2] == "FIS"           # Department
    assert first[3] == "SHL"           # Branch
    assert first[4] == "USD"           # Cost Currency
    assert first[5] == "0.00"          # Estimated Cost
    assert first[6] == "8600.00"       # OS Cost Amt
    assert first[7] == "0.00"          # Local Cost Amt
    assert first[8] == "CNSHL"         # Creditor
    assert first[9] == "CNY"           # Sell Currency
    assert first[10] == "61400.00"     # OS Sell Amt
    assert first[11] == "61400.00"     # Estimated Revenue
    assert first[12] == "61400.00"     # Local Sell Amt
    assert first[13] == "CNSHO"        # Debtor

    second = rows[2]
    assert second[0] == "OCUC"
    assert second[1] == "清关费"
    assert second[5] == "2280.00"      # 应付币种是 CNY：估算成本
    assert second[6] == "2280.00"      # 应付币种是 CNY：应付金额
    assert second[11] == "0.00"        # 应收币种是 USD


def test_amounts_have_no_thousands_separator(client, admin_headers,
                                              seeded_shipment, seeded_charge):
    """金额不带千分位逗号——CSV 里只有文本，带逗号就没法求和了。"""
    r = client.get(f"/api/v1/shipments/{seeded_shipment.id}/charge-infos/export",
                   headers=admin_headers)
    assert r.status_code == 200
    rows = _load(r.content)
    for cell in rows[1]:
        assert "," not in cell or cell == ""


def test_export_skips_deleted_charge_info(client, admin_headers,
                                          seeded_shipment, seeded_charge):
    assert client.delete(f"/api/v1/charge-infos/{seeded_charge.id}",
                         headers=admin_headers).status_code == 200
    r = client.get(f"/api/v1/shipments/{seeded_shipment.id}/charge-infos/export",
                   headers=admin_headers)
    assert r.status_code == 200
    rows = _load(r.content)
    assert len(rows) == 1        # 只剩表头


def test_export_of_missing_shipment_is_404(client, admin_headers):
    r = client.get("/api/v1/shipments/999999/charge-infos/export",
                   headers=admin_headers)
    assert r.status_code == 404
