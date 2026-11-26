"""导出的 Excel：英文表头、内容与金额类型。"""
from io import BytesIO

from openpyxl import load_workbook


def _load(content: bytes):
    return load_workbook(BytesIO(content)).active


def test_export_returns_xlsx_with_english_headers(client, admin_headers,
                                                  seeded_shipment, seeded_charge):
    r = client.get(f"/api/v1/shipments/{seeded_shipment.id}/charge-infos/export",
                   headers=admin_headers)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    assert "charge-info" in r.headers["content-disposition"]
    assert "attachment" in r.headers["content-disposition"]

    ws = _load(r.content)
    headers = [c.value for c in ws[1]]
    assert headers == [
        "Charge Code", "Description", "Branch", "Department",
        "Cost Currency", "OS Cost Amt", "Estimated Cost",
        "Local Cost Amt", "Creditor", "Sell Currency", "OS Sell Amt",
        "Estimated Revenue", "Local Sell Amt", "Debtor",
    ]


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
    ws = _load(r.content)
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    assert len(rows) == 2

    first = rows[0]
    assert first[0] == "DHLF"                        # Charge Code
    assert first[1] == "快递国际"                     # Description
    assert first[2] == "SHL"                         # Branch
    assert first[3] == "FIS"                         # Department
    assert first[4] == "USD"                         # Cost Currency
    assert first[5] == 8600                          # OS Cost Amt 是数字
    assert first[6] == 0                             # Estimated Cost 是数字
    assert first[7] == 0                             # Local Cost Amt 是数字
    assert first[8] == "CNSHL"                       # Creditor
    assert first[9] == "CNY"                         # Sell Currency
    assert first[10] == 61400                        # OS Sell Amt 是数字
    assert first[11] == 61400                        # Estimated Revenue 是数字
    assert first[12] == 61400                        # Local Sell Amt 是数字
    assert first[13] == "CNSHO"                      # Debtor

    second = rows[1]
    assert second[0] == "OCUC"
    assert second[1] == "清关费"
    assert second[6] == 2280                         # 应付币种是 CNY
    assert second[11] == 0                           # 应收币种是 USD


def test_export_skips_deleted_charge_info(client, admin_headers,
                                          seeded_shipment, seeded_charge):
    assert client.delete(f"/api/v1/charge-infos/{seeded_charge.id}",
                         headers=admin_headers).status_code == 200
    r = client.get(f"/api/v1/shipments/{seeded_shipment.id}/charge-infos/export",
                   headers=admin_headers)
    assert r.status_code == 200
    ws = _load(r.content)
    assert list(ws.iter_rows(min_row=2, values_only=True)) == []


def test_export_of_missing_shipment_is_404(client, admin_headers):
    r = client.get("/api/v1/shipments/999999/charge-infos/export",
                   headers=admin_headers)
    assert r.status_code == 404
