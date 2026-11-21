"""端到端冒烟：选项维护闭环（design D26 / tasks 16.4）。"""


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


def test_option_lifecycle_from_candidate_to_delete(client, admin_user, seeded_options):
    headers = _login(client)

    # 1. 新增一个应付部门值
    r = client.post("/api/v1/options/departments", headers=headers,
                    json={"code": "FNEW", "name": "新部门"})
    assert r.status_code == 201, r.text
    opt_id = r.json()["id"]

    # 2. 它立刻出现在候选列表里，且可以用于录入
    kinds = client.get("/api/v1/options/candidates", headers=headers).json()["kinds"]
    assert "FNEW" in [o["code"] for o in kinds["departments"]]

    sid = client.post("/api/v1/shipments", headers=headers,
                      json={"shipment_num": "SH-E2E-OPT"}).json()["id"]
    r = client.post(f"/api/v1/shipments/{sid}/charge-infos", headers=headers,
                    json=_charge_payload(department="FNEW"))
    assert r.status_code == 201, r.text
    # 一次写入两条，两条的部门都是 FNEW
    cid = r.json()["items"][0]["id"]

    # 3. 停用后它从候选列表消失
    r = client.patch(f"/api/v1/options/departments/{opt_id}/status",
                     headers=headers, json={"is_active": False})
    assert r.status_code == 200
    kinds = client.get("/api/v1/options/candidates", headers=headers).json()["kinds"]
    assert "FNEW" not in [o["code"] for o in kinds["departments"]]

    # 4. 但引用了它的已有记录仍能正常编辑保存（保留原值）
    r = client.patch(f"/api/v1/charge-infos/{cid}", headers=headers,
                     json={"department": "FNEW", "os_cost_amt": "1500.00"})
    assert r.status_code == 200, r.text
    assert r.json()["os_cost_amt"] == "1500.00"
    assert r.json()["department"] == "FNEW"

    # 5. 删除前的引用数量预检
    r = client.get(f"/api/v1/options/departments/{opt_id}/references",
                   headers=headers)
    assert r.status_code == 200
    assert r.json()["referenced"] == 2

    # 6. 删除后，引用它的记录再保存被拒绝
    r = client.delete(f"/api/v1/options/departments/{opt_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["referenced"] == 2

    r = client.patch(f"/api/v1/charge-infos/{cid}", headers=headers,
                     json={"department": "FNEW", "os_cost_amt": "1600.00"})
    assert r.status_code == 422
    assert "已被删除" in r.json()["detail"]


def test_option_code_is_immutable_and_unique(client, admin_user, seeded_options):
    headers = _login(client)
    r = client.post("/api/v1/options/departments", headers=headers,
                    json={"code": "FIS"})
    assert r.status_code == 409  # 同一张表内 code 重复

    listed = client.get("/api/v1/options/departments", headers=headers).json()
    fis = next(o for o in listed["items"] if o["code"] == "FIS")
    r = client.patch(f"/api/v1/options/departments/{fis['id']}", headers=headers,
                     json={"code": "FIS2", "name": "改名"})
    assert r.status_code == 409
    assert "不可修改" in r.json()["detail"]


def test_admin_list_carries_reference_count(client, admin_user, seeded_options):
    headers = _login(client)
    sid = client.post("/api/v1/shipments", headers=headers,
                      json={"shipment_num": "SH-E2E-REF"}).json()["id"]
    client.post(f"/api/v1/shipments/{sid}/charge-infos", headers=headers,
                json=_charge_payload())

    listed = client.get("/api/v1/options/currencies", headers=headers).json()
    counts = {o["code"]: o["referenced"] for o in listed["items"]}
    # 一次写入两条：A 的应付侧与应收侧都是 USD，B 的应付侧也是 USD，
    # 所以 USD 被引用 3 次；CNY 只出现在 B 的应收侧，被引用 1 次
    assert counts.get("USD") == 3
    assert counts.get("CNY") == 1
    assert counts.get("EUR") == 0
