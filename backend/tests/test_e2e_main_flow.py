"""端到端冒烟：主链路（design D26 / tasks 16.2）。

以管理员身份走一遍「登录 → 建订单 → 录费用信息 → 核对明细 → 软删除」，
每一步都断言真实的接口行为，而不是只断言状态码。
"""


def _login(client, phone="13800000001"):
    r = client.post("/api/v1/auth/login", json={"phone": phone})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _charge_payload(**over):
    payload = {
        "charge_code": "DHLF",
        "department": "FIS",
        "branch": "SHL",
        "cost_currency": "USD",
        "os_cost_amt": "1200.00",
        "creditor": "CNSHL",
        "sell_currency": "CNY",
        "os_sell_amt": "8600.00",
        "debtor": "CNSHO",
    }
    payload.update(over)
    return payload


def test_main_flow_login_to_soft_delete(client, admin_user, seeded_options):
    headers = _login(client)

    # 1. 新建货运订单
    r = client.post("/api/v1/shipments", headers=headers,
                    json={"shipment_num": "SH-E2E-0001"})
    assert r.status_code == 201, r.text
    sid = r.json()["id"]

    # 2. 重复的货运订单号被拒绝，大小写变体同样被拒
    assert client.post("/api/v1/shipments", headers=headers,
                       json={"shipment_num": "SH-E2E-0001"}).status_code == 409
    assert client.post("/api/v1/shipments", headers=headers,
                       json={"shipment_num": "sh-e2e-0001"}).status_code == 409

    # 3. 录入一条费用信息：一次写入两条，任务码自动等于所属订单号
    r = client.post(f"/api/v1/shipments/{sid}/charge-infos", headers=headers,
                    json=_charge_payload())
    assert r.status_code == 201, r.text
    lines = r.json()["items"]
    assert len(lines) == 2
    for line in lines:
        assert line["job_num"] == "SH-E2E-0001"
    cids = [line["id"] for line in lines]

    # 4. 分类字段打错值被后端拒绝
    r = client.post(f"/api/v1/shipments/{sid}/charge-infos", headers=headers,
                    json=_charge_payload(department="FIS5"))
    assert r.status_code == 422
    assert "无效" in r.json()["detail"]

    # 5. 详情给出该单的费用信息明细，且不做金额合计
    r = client.get(f"/api/v1/shipments/{sid}", headers=headers)
    assert r.status_code == 200
    detail = r.json()
    assert len(detail["charge_info"]) == 2
    a = next(l for l in detail["charge_info"] if l["branch"] == "SHL")
    assert a["cost_currency"] == "USD"
    assert a["os_cost_amt"] == "1200.00"
    assert a["sell_currency"] == "USD"      # 由应付侧推出
    assert a["os_sell_amt"] == "1200.00"
    assert a["debtor"] == "CNSHO"
    b = next(l for l in detail["charge_info"] if l["branch"] == "SHO")
    assert b["sell_currency"] == "CNY"
    assert b["os_sell_amt"] == "8600.00"
    assert "cost_totals" not in detail
    assert "sell_totals" not in detail

    # 6. 软删掉这两条费用信息后，详情里不再出现
    for cid in cids:
        assert client.delete(f"/api/v1/charge-infos/{cid}",
                             headers=headers).status_code == 200
    detail = client.get(f"/api/v1/shipments/{sid}", headers=headers).json()
    assert detail["charge_info"] == []

    # 7. 软删除货运订单后，整单不可见
    assert client.delete(f"/api/v1/shipments/{sid}",
                         headers=headers).status_code == 200
    assert client.get(f"/api/v1/shipments/{sid}",
                      headers=headers).status_code == 404
    listed = client.get("/api/v1/shipments", headers=headers).json()
    assert all(i["id"] != sid for i in listed["items"])


def test_main_flow_shipment_list_has_no_amounts(client, admin_user, seeded_options):
    headers = _login(client)
    client.post("/api/v1/shipments", headers=headers,
                json={"shipment_num": "SH-E2E-0003"})
    body = client.get("/api/v1/shipments", headers=headers).text
    assert "os_cost_amt" not in body
    assert "os_sell_amt" not in body
    assert "cost_totals" not in body
    assert "sell_totals" not in body
