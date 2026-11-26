"""费用信息新增的四个折算后金额与描述（design D32）。

规则（按每条记录**自己**的币种算）：
- 应付币种是 CNY：估算成本 = 本地成本 = 该条的应付金额；否则都是 0.00
- 应收币种是 CNY：估算收入 = 本地应收金额 = 该条的应收金额；否则都是 0.00
- 描述取页面填的值；没填时从费用代码表带出该 code 的描述
"""
from decimal import Decimal

import pytest


def _payload(**over):
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


def _create(client, headers, shipment, **over):
    r = client.post(f"/api/v1/shipments/{shipment.id}/charge-infos",
                    headers=headers, json=_payload(**over))
    assert r.status_code == 201, r.text
    return r.json()["items"]


@pytest.mark.parametrize("cost_currency,sell_currency,expected", [
    # 应付币种是 CNY：估算成本 = 本地成本 = 应付金额；否则都是 0.00
    ("CNY", "USD", {
        "a": ("1200.00", "1200.00", "1200.00", "1200.00"),
        "b": ("1200.00", "1200.00", "0.00", "0.00"),
    }),
    ("USD", "CNY", {
        "a": ("0.00", "0.00", "0.00", "0.00"),
        "b": ("0.00", "0.00", "8600.00", "8600.00"),
    }),
    ("CNY", "CNY", {
        "a": ("1200.00", "1200.00", "1200.00", "1200.00"),
        "b": ("1200.00", "1200.00", "8600.00", "8600.00"),
    }),
    ("USD", "USD", {
        "a": ("0.00", "0.00", "0.00", "0.00"),
        "b": ("0.00", "0.00", "0.00", "0.00"),
    }),
])
def test_estimated_amounts_follow_the_currency(client, admin_headers,
                                               seeded_shipment, seeded_options,
                                               cost_currency, sell_currency,
                                               expected):
    """四个折算后金额按各自币种算：CNY 才等于原币金额，其余 0.00。"""
    items = _create(client, admin_headers, seeded_shipment,
                    cost_currency=cost_currency, sell_currency=sell_currency)
    a, b = items
    for item, key in ((a, "a"), (b, "b")):
        est_cost, local_cost, est_rev, local_sell = expected[key]
        assert item["estimated_cost"] == est_cost, key
        assert item["local_cost_amt"] == local_cost, key
        assert item["estimated_revenue"] == est_rev, key
        assert item["local_sell_amt"] == local_sell, key


def test_estimated_amounts_are_zero_not_null(client, admin_headers,
                                              seeded_shipment, seeded_options):
    """非本位币的折算金额是 0.00，不是空值。"""
    items = _create(client, admin_headers, seeded_shipment,
                    cost_currency="USD", sell_currency="USD")
    for item in items:
        assert item["estimated_cost"] == "0.00"
        assert item["local_cost_amt"] == "0.00"
        assert item["estimated_revenue"] == "0.00"
        assert item["local_sell_amt"] == "0.00"


def test_description_is_the_one_filled_in_the_form(client, admin_headers,
                                                   seeded_shipment, seeded_options):
    """两条记录的描述都是页面填的那个。"""
    items = _create(client, admin_headers, seeded_shipment,
                    description="页面上改过的描述")
    assert items[0]["description"] == "页面上改过的描述"
    assert items[1]["description"] == "页面上改过的描述"


def test_description_falls_back_to_the_charge_code_option(client, admin_headers,
                                                          db, seeded_shipment,
                                                          seeded_options):
    """页面没填描述时，从费用代码表带出该 code 的描述。"""
    from app.models import ChargeCode
    cc = db.query(ChargeCode).filter(ChargeCode.code == "DHLF").first()
    cc.description = "快递国际"
    db.flush()

    items = _create(client, admin_headers, seeded_shipment)
    assert items[0]["description"] == "快递国际"
    assert items[1]["description"] == "快递国际"


def test_editing_the_currency_recalculates_the_estimated_amounts(
        client, admin_headers, seeded_shipment, seeded_options):
    """改币种或金额后，四个折算后金额跟着重算。"""
    items = _create(client, admin_headers, seeded_shipment,
                    cost_currency="USD", sell_currency="USD")
    line = items[0]
    assert line["estimated_cost"] == "0.00"

    r = client.patch(f"/api/v1/charge-infos/{line['id']}", headers=admin_headers,
                     json={"cost_currency": "CNY", "os_cost_amt": "500.00"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["estimated_cost"] == "500.00"
    assert body["local_cost_amt"] == "500.00"
    # 应收币种没改，仍是 USD
    assert body["estimated_revenue"] == "0.00"
    assert body["local_sell_amt"] == "0.00"


def test_amounts_are_stored_as_two_decimal_numbers(client, admin_headers, db,
                                                    seeded_shipment,
                                                    seeded_options):
    """落库的是两位小数的金额（0.00 而不是 0）。"""
    items = _create(client, admin_headers, seeded_shipment,
                    cost_currency="USD", sell_currency="USD")
    from app.models import ChargeInfo
    row = db.query(ChargeInfo).filter(ChargeInfo.id == items[0]["id"]).first()
    assert row.estimated_cost == Decimal("0.00")
    assert row.local_cost_amt == Decimal("0.00")
    assert row.estimated_revenue == Decimal("0.00")
    assert row.local_sell_amt == Decimal("0.00")
