"""费用代码表的标签列是描述（description），其余五类仍是名称（name）。"""
import pytest


@pytest.mark.parametrize("kind,label_field", [
    ("charge_codes", "description"),
    ("departments", "name"),
    ("branches", "name"),
    ("currencies", "name"),
    ("creditors", "name"),
    ("debtors", "name"),
])
def test_create_uses_the_kind_s_label_column(client, admin_headers,
                                             seeded_options, kind, label_field):
    """新增时只认本类的那一列，另一列被忽略。"""
    other = "name" if label_field == "description" else "description"
    r = client.post(f"/api/v1/options/{kind}", headers=admin_headers,
                    json={"code": "NEWOPT", label_field: "写对的标签",
                          other: "写错的列"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body[label_field] == "写对的标签"
    assert body[other] is None


def test_charge_code_falls_back_to_code_when_description_is_empty(
        client, admin_headers, seeded_options):
    """描述留空时以代码呈现。"""
    r = client.post("/api/v1/options/charge_codes", headers=admin_headers,
                    json={"code": "NODESC"})
    assert r.status_code == 201, r.text
    assert r.json()["description"] == "NODESC"
    assert r.json()["name"] is None


def test_charge_code_candidate_search_matches_description(client, admin_headers,
                                                           seeded_options):
    """候选列表按描述过滤（费用代码表没有 name 列，过滤不能报错）。"""
    client.post("/api/v1/options/charge_codes", headers=admin_headers,
                json={"code": "SRCH", "description": "海运附加费"})
    r = client.get("/api/v1/options/charge_codes/options", headers=admin_headers,
                   params={"q": "海运"})
    assert r.status_code == 200, r.text
    assert any(o["code"] == "SRCH" for o in r.json()["items"])

    r = client.get("/api/v1/options/charge_codes/options", headers=admin_headers,
                   params={"q": "SRCH"})
    assert r.status_code == 200
    assert any(o["code"] == "SRCH" for o in r.json()["items"])


def test_clearing_the_label_falls_back_to_code(client, admin_headers,
                                                seeded_options):
    """标签传空 = 清空，页面上以代码呈现；不带这个字段则保持原值。"""
    r = client.post("/api/v1/options/charge_codes", headers=admin_headers,
                    json={"code": "CLR", "description": "有描述"})
    opt_id = r.json()["id"]

    # 显式传空 → 清空
    r = client.patch(f"/api/v1/options/charge_codes/{opt_id}",
                     headers=admin_headers, json={"code": "CLR",
                                                 "description": None})
    assert r.status_code == 200, r.text
    assert r.json()["description"] == "CLR"

    # 先改回有描述，再用一个不带标签字段的请求 → 原值不动
    client.patch(f"/api/v1/options/charge_codes/{opt_id}", headers=admin_headers,
                 json={"code": "CLR", "description": "有描述"})
    r = client.patch(f"/api/v1/options/charge_codes/{opt_id}",
                     headers=admin_headers, json={"code": "CLR"})
    assert r.status_code == 200, r.text
    assert r.json()["description"] == "有描述"


def test_other_kinds_keep_the_name_column(client, admin_headers, seeded_options):
    """其余五类不受影响：标签仍在 name 上，description 为空。"""
    r = client.post("/api/v1/options/departments", headers=admin_headers,
                    json={"code": "NAMED", "name": "某部门"})
    assert r.status_code == 201, r.text
    assert r.json()["name"] == "某部门"
    assert r.json()["description"] is None
