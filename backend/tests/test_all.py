"""核心测试：认证、权限、用户管理、选项、货运订单、费用信息、关联生成。

覆盖任务 3.x / 4.x / 5.x / 6.x / 7.x / 8.x / 9.x / 10.1 的验证点。
"""
import pytest
from decimal import Decimal


# ========================================================= 认证（auth）

def test_login_with_phone_only(client, admin_user):
    r = client.post("/api/v1/auth/login", json={"phone": admin_user.phone})
    assert r.status_code == 200
    body = r.json()
    assert body["token"]
    assert body["user"]["authority"] == "admin"
    assert "password" not in str(body)


def test_login_unknown_phone(client):
    r = client.post("/api/v1/auth/login", json={"phone": "11111111111"})
    assert r.status_code == 401


def test_login_disabled_user(client, db, admin_user):
    admin_user.is_active = False
    db.flush()
    r = client.post("/api/v1/auth/login", json={"phone": admin_user.phone})
    assert r.status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_with_token(client, admin_headers):
    r = client.get("/api/v1/auth/me", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["authority"] == "admin"


def test_tampered_token_rejected(client):
    r = client.get("/api/v1/auth/me",
                   headers={"Authorization": "Bearer garbage.token.here"})
    assert r.status_code == 401


# ========================================================= 权限（实时判定）

def test_normal_user_forbidden_on_user_list(client, normal_headers):
    assert client.get("/api/v1/users", headers=normal_headers).status_code == 403


def test_normal_user_can_read_candidates(client, normal_headers, seeded_options):
    r = client.get("/api/v1/options/candidates", headers=normal_headers)
    assert r.status_code == 200


def test_normal_user_forbidden_on_option_write(client, normal_headers, seeded_options):
    r = client.post("/api/v1/options/departments", json={"code": "NEWX"},
                    headers=normal_headers)
    assert r.status_code == 403


def test_permission_change_takes_effect_immediately(client, db, normal_headers,
                                                    normal_user):
    normal_user.authority = "admin"
    db.flush()
    r = client.get("/api/v1/users", headers=normal_headers)
    assert r.status_code == 200


def test_disable_takes_effect_immediately(client, db, normal_headers, normal_user):
    normal_user.is_active = False
    db.flush()
    r = client.get("/api/v1/auth/me", headers=normal_headers)
    assert r.status_code == 401


# ========================================================= 用户管理

def test_create_user_validation(client, admin_headers):
    ok = client.post("/api/v1/users", headers=admin_headers,
                     json={"phone": "13700000003", "username": "王磊",
                           "authority": "normal"})
    assert ok.status_code == 201
    dup = client.post("/api/v1/users", headers=admin_headers,
                      json={"phone": "13700000003", "username": "重复",
                            "authority": "normal"})
    assert dup.status_code == 409
    bad_phone = client.post("/api/v1/users", headers=admin_headers,
                            json={"phone": "138abc", "username": "x",
                                  "authority": "normal"})
    assert bad_phone.status_code == 422
    bad_auth = client.post("/api/v1/users", headers=admin_headers,
                           json={"phone": "13700000004", "username": "x",
                                 "authority": "boss"})
    assert bad_auth.status_code == 422


def test_user_list_filters(client, admin_headers, normal_user):
    r = client.get("/api/v1/users", headers=admin_headers,
                   params={"authority": "normal"})
    assert r.status_code == 200
    assert all(u["authority"] == "normal" for u in r.json()["items"])
    r2 = client.get("/api/v1/users", headers=admin_headers,
                    params={"keyword": "13900000002"})
    assert any(u["phone"] == "13900000002" for u in r2.json()["items"])


def test_update_user_phone_dup_rejected(client, admin_headers, db,
                                        admin_user, normal_user):
    r = client.patch(f"/api/v1/users/{normal_user.id}", headers=admin_headers,
                     json={"phone": admin_user.phone, "username": "x",
                           "authority": "normal"})
    assert r.status_code == 409


def test_cannot_disable_self(client, admin_headers, admin_user):
    r = client.patch(f"/api/v1/users/{admin_user.id}/status", headers=admin_headers,
                     json={"is_active": False})
    assert r.status_code == 409


def test_delete_user_soft(client, admin_headers, db, normal_user, seeded_shipment):
    r = client.delete(f"/api/v1/users/{normal_user.id}", headers=admin_headers)
    assert r.status_code == 200
    assert normal_user.status == 1
    # 其创建的数据不受影响
    assert seeded_shipment.status == 0


# ========================================================= 选项（option-lists）

def test_option_code_unique_per_table(client, admin_headers, seeded_options):
    r = client.post("/api/v1/options/departments", headers=admin_headers,
                    json={"code": "NEWDEPT"})
    assert r.status_code == 201
    assert r.json()["name"] == "NEWDEPT"  # 名称缺省时以代码呈现
    r2 = client.post("/api/v1/options/departments", headers=admin_headers,
                     json={"code": "NEWDEPT"})
    assert r2.status_code == 409
    # 六类各自独立：charge_codes 里没有 FIS
    r3 = client.get("/api/v1/options/charge_codes/options",
                    headers=admin_headers)
    assert all(o["code"] != "FIS" for o in r3.json()["items"])


def test_option_code_immutable(client, admin_headers, seeded_options, db):
    from app.models import Department
    d = db.query(Department).filter_by(code="FIS").first()
    r = client.patch(f"/api/v1/options/departments/{d.id}", headers=admin_headers,
                     json={"code": "FIS2"})
    assert r.status_code == 409


def test_option_disable_and_candidates(client, admin_headers, db, seeded_options):
    from app.models import Currency
    c = db.query(Currency).filter_by(code="USD").first()
    r = client.patch(f"/api/v1/options/currencies/{c.id}/status",
                     headers=admin_headers, json={"is_active": False})
    assert r.status_code == 200
    lst = client.get("/api/v1/options/currencies/options",
                     headers=admin_headers).json()["items"]
    assert all(o["code"] != "USD" for o in lst)
    # 停用项仍可在管理列表查询到
    admin_lst = client.get("/api/v1/options/currencies",
                           headers=admin_headers,
                           params={"include_deleted": True}).json()["items"]
    assert any(o["code"] == "USD" for o in admin_lst)


def test_admin_list_excludes_deleted_by_default(client, admin_headers, db,
                                                seeded_options):
    """管理列表默认在服务端就过滤掉已软删除的项。"""
    from app.models import ChargeCode
    c = db.query(ChargeCode).filter_by(code="DHLF").first()
    assert client.delete(f"/api/v1/options/charge_codes/{c.id}",
                         headers=admin_headers).status_code == 200

    # 默认请求：已删除的项不返回
    lst = client.get("/api/v1/options/charge_codes", headers=admin_headers).json()
    assert all(o["code"] != "DHLF" for o in lst["items"])
    # 显式要求时才带出来（供追溯删除记录用）
    lst_all = client.get("/api/v1/options/charge_codes", headers=admin_headers,
                         params={"include_deleted": True}).json()["items"]
    assert any(o["code"] == "DHLF" for o in lst_all)


def test_option_delete_returns_reference_count(client, admin_headers, db,
                                               seeded_options, seeded_charge):
    from app.models import ChargeCode
    c = db.query(ChargeCode).filter_by(code="DHLF").first()
    r = client.delete(f"/api/v1/options/charge_codes/{c.id}", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["referenced"] >= 1


def test_candidates_route_not_shadowed(client, admin_headers, seeded_options):
    r = client.get("/api/v1/options/candidates", headers=admin_headers)
    assert r.status_code == 200
    assert "kinds" in r.json()


def test_option_kinds_are_exactly_six(client, admin_headers, seeded_options):
    """六类选项定稿；描述/应付税率/账单类型三张表已随字段删除而移除。"""
    kinds = client.get("/api/v1/options/candidates",
                       headers=admin_headers).json()["kinds"]
    assert set(kinds) == {
        "charge_codes", "departments", "branches",
        "currencies", "creditors", "debtors",
    }
    for kind in ("descriptions", "cost_tax_ids", "inv_types"):
        r = client.get(f"/api/v1/options/{kind}", headers=admin_headers)
        assert r.status_code == 404


# ========================================================= 货运订单

def test_shipment_num_uniqueness(client, admin_headers, seeded_shipment):
    r = client.post("/api/v1/shipments", headers=admin_headers,
                    json={"shipment_num": "SH-20261119-0007"})
    assert r.status_code == 409
    r2 = client.post("/api/v1/shipments", headers=admin_headers,
                     json={"shipment_num": "sh-20261119-0007"})
    assert r2.status_code == 409  # 大小写不敏感
    r3 = client.post("/api/v1/shipments", headers=admin_headers,
                     json={"shipment_num": "  sh-20261119-0007  "})
    assert r3.status_code == 409  # 忽略首尾空格
    empty = client.post("/api/v1/shipments", headers=admin_headers,
                        json={"shipment_num": "   "})
    assert empty.status_code == 422


def test_shipment_create_and_list(client, admin_headers):
    r = client.post("/api/v1/shipments", headers=admin_headers,
                    json={"shipment_num": "SH-TEST-001"})
    assert r.status_code == 201
    assert r.json()["lifecycle"] == "draft"
    lst = client.get("/api/v1/shipments", headers=admin_headers).json()
    assert all("os_cost_amt" not in str(i) for i in lst["items"])
    assert all("charge_info_count" in i for i in lst["items"])
    # 列表不返回应付/应收合计
    assert all("cost_totals" not in i and "sell_totals" not in i
               for i in lst["items"])


def test_shipment_lifecycle_transitions(client, admin_headers, db,
                                        admin_user, seeded_shipment):
    sid = seeded_shipment.id
    assert client.post(f"/api/v1/shipments/{sid}/confirm",
                       headers=admin_headers).status_code == 200
    assert seeded_shipment.lifecycle == "confirmed"
    assert client.post(f"/api/v1/shipments/{sid}/complete",
                       headers=admin_headers).status_code == 200
    assert seeded_shipment.lifecycle == "completed"
    # 终态不能再流转
    assert client.post(f"/api/v1/shipments/{sid}/cancel",
                       headers=admin_headers).status_code == 409
    assert client.post(f"/api/v1/shipments/{sid}/confirm",
                       headers=admin_headers).status_code == 409


def test_shipment_soft_delete(client, admin_headers, db, seeded_charge,
                              seeded_shipment):
    r = client.delete(f"/api/v1/shipments/{seeded_shipment.id}",
                      headers=admin_headers)
    assert r.status_code == 200
    assert seeded_shipment.status == 1
    assert seeded_charge.status == 0  # 明细不做级联写入
    assert client.get(f"/api/v1/shipments/{seeded_shipment.id}",
                      headers=admin_headers).status_code == 404


def test_shipment_list_filters(client, admin_headers, db, admin_user):
    from app.models import Shipment
    db.add(Shipment(shipment_num="ABC-999", status=0, operator=admin_user.phone))
    db.flush()
    r = client.get("/api/v1/shipments", headers=admin_headers,
                   params={"keyword": "abc"})
    assert any(s["shipment_num"] == "ABC-999" for s in r.json()["items"])
    r2 = client.get("/api/v1/shipments", headers=admin_headers,
                    params={"keyword": "zzz-not-exist"})
    assert r2.json()["items"] == [] and r2.json()["total"] == 0


# ========================================================= 费用信息

def _payload(**over):
    base = {"charge_code": "DHLF", "department": "FIS", "branch": "SHL",
            "cost_currency": "USD", "os_cost_amt": "1200.00", "creditor": "CNSHL",
            "sell_currency": "CNY", "os_sell_amt": "8600.00", "debtor": "CNSHO"}
    base.update(over)
    return base


def test_charge_info_create_writes_pair(client, admin_headers, seeded_shipment):
    """新增一条费用信息会写入两条：A（应付侧）与 B（镜像分支那条）。"""
    r = client.post(f"/api/v1/shipments/{seeded_shipment.id}/charge-infos",
                    headers=admin_headers, json=_payload())
    assert r.status_code == 201, r.text
    items = r.json()["items"]
    assert len(items) == 2

    a, b = items
    # A：页面填的应付侧 + 推出的应收侧
    assert a["charge_code"] == "DHLF"
    assert a["department"] == "FIS"
    assert a["branch"] == "SHL"
    assert a["cost_currency"] == "USD"
    assert a["os_cost_amt"] == "1200.00"
    assert a["creditor"] == "CNSHL"
    assert a["sell_currency"] == "USD"      # = A.cost_currency
    assert a["os_sell_amt"] == "1200.00"   # = A.os_cost_amt
    assert a["debtor"] == "CNSHO"          # SHL 的对家

    # B：由 A 推出的应付侧 + 页面填的应收侧
    assert b["charge_code"] == "DHLF"
    assert b["department"] == "FIS"
    assert b["branch"] == "SHO"             # SHL 的镜像分支
    assert b["cost_currency"] == "USD"      # = A.sell_currency
    assert b["os_cost_amt"] == "1200.00"   # = A.os_sell_amt
    assert b["creditor"] == "CNSHO"         # 对家单位
    assert b["sell_currency"] == "CNY"      # 页面填写
    assert b["os_sell_amt"] == "8600.00"   # 页面填写
    assert b["debtor"] == "CNSHO"           # 页面填写
    # 不变量：对家单位——A 的应收对象与 B 的应付对象是同一个
    assert b["creditor"] == a["debtor"] == "CNSHO"

    # 两条的任务码都等于所属订单号
    assert a["job_num"] == seeded_shipment.shipment_num
    assert b["job_num"] == seeded_shipment.shipment_num


def test_charge_info_create_sho_branch(client, admin_headers, seeded_shipment):
    """分支为 SHO 时，镜像关系反过来：A 的对家是 CNSHL，B 的分支是 SHL。"""
    r = client.post(f"/api/v1/shipments/{seeded_shipment.id}/charge-infos",
                    headers=admin_headers,
                    json=_payload(branch="SHO", creditor="CNSHO",
                                  debtor="CNSHO"))
    assert r.status_code == 201, r.text
    a, b = r.json()["items"]
    assert a["branch"] == "SHO"
    assert a["debtor"] == "CNSHL"
    assert b["branch"] == "SHL"
    assert b["creditor"] == "CNSHL"
    # 不变量：对家单位——A 的应收对象与 B 的应付对象是同一个
    assert b["creditor"] == a["debtor"] == "CNSHL"


def test_charge_info_create_rejects_unknown_branch(client, admin_headers,
                                                    seeded_shipment):
    """没有镜像分支的分支直接拒绝，不写入任何记录。"""
    r = client.post(f"/api/v1/shipments/{seeded_shipment.id}/charge-infos",
                    headers=admin_headers, json=_payload(branch="XXX"))
    assert r.status_code == 422
    assert "SHL" in r.json()["detail"]
    detail = client.get(f"/api/v1/shipments/{seeded_shipment.id}",
                        headers=admin_headers).json()
    assert detail["charge_info"] == []


def test_charge_info_missing_side_rejected(client, admin_headers, seeded_shipment):
    p = _payload(os_sell_amt=None, sell_currency=None, debtor=None)
    p = {k: v for k, v in p.items() if v is not None}
    r = client.post(f"/api/v1/shipments/{seeded_shipment.id}/charge-infos",
                    headers=admin_headers, json=p)
    assert r.status_code == 422


def test_charge_info_amount_validation(client, admin_headers, seeded_shipment):
    r = client.post(f"/api/v1/shipments/{seeded_shipment.id}/charge-infos",
                    headers=admin_headers, json=_payload(os_cost_amt="100.125"))
    assert r.status_code == 422  # 三位小数
    r2 = client.post(f"/api/v1/shipments/{seeded_shipment.id}/charge-infos",
                     headers=admin_headers, json=_payload(os_cost_amt="-5"))
    assert r2.status_code == 422  # 负数


def test_charge_info_invalid_option_rejected(client, admin_headers, seeded_shipment):
    r = client.post(f"/api/v1/shipments/{seeded_shipment.id}/charge-infos",
                    headers=admin_headers, json=_payload(department="FIS5"))
    assert r.status_code == 422  # 取值不存在


def test_charge_info_edit_updates_job_num_not(client, admin_headers, seeded_charge):
    r = client.patch(f"/api/v1/charge-infos/{seeded_charge.id}",
                     headers=admin_headers, json={"os_cost_amt": "999.00"})
    assert r.status_code == 200
    assert Decimal(str(seeded_charge.os_cost_amt)) == 999
    assert seeded_charge.job_num == "SH-20261119-0007"  # 不变


def test_charge_info_soft_delete(client, admin_headers, seeded_charge):
    r = client.delete(f"/api/v1/charge-infos/{seeded_charge.id}",
                      headers=admin_headers)
    assert r.status_code == 200
    assert seeded_charge.status == 1


def test_detail_returns_no_totals(client, admin_headers, seeded_shipment,
                                  seeded_charge):
    """详情接口不做金额合计——合计带已从界面上移除。"""
    r = client.get(f"/api/v1/shipments/{seeded_shipment.id}",
                   headers=admin_headers)
    assert r.status_code == 200
    body = r.json()
    assert "cost_totals" not in body
    assert "sell_totals" not in body
    # 明细本身仍然完整
    assert len(body["charge_info"]) == 1
    assert body["charge_info"][0]["os_cost_amt"] == "8600.00"


def test_disabled_option_edit_keep_passes_but_create_rejected(
        client, admin_headers, db, seeded_charge, seeded_options):
    from app.models import Currency
    cur = db.query(Currency).filter_by(code="USD").first()
    client.patch(f"/api/v1/options/currencies/{cur.id}/status",
                 headers=admin_headers, json={"is_active": False})
    # 编辑保留已停用的原值：通过
    r1 = client.patch(f"/api/v1/charge-infos/{seeded_charge.id}",
                      headers=admin_headers, json={"os_cost_amt": "500.00"})
    assert r1.status_code == 200
    # 新建使用已停用值：拒绝
    r2 = client.post(f"/api/v1/shipments/{seeded_charge.shipment_id}/charge-infos",
                     headers=admin_headers, json=_payload())
    assert r2.status_code == 422
