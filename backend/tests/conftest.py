"""测试夹具：独立测试库 + client fixture + 种子数据。

每个测试用例在事务回滚中运行（函数级隔离，不污染开发库）。
"""
import os
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.security import create_token
from app.db.base import Base
from app.main import app

# 测试库连接串：默认从应用配置派生（仅替换库名），也可用 TEST_DATABASE_URL 覆盖。
# 派生而非硬编码，是为了让测试与应用共用同一套主机与凭据配置。
_override = os.environ.get("TEST_DATABASE_URL")
if _override:
    TEST_DB_URL = _override
else:
    _BASE_URL = get_settings().DATABASE_URL
    TEST_DB_URL = re.sub(r"/[^/?]+(\?|$)", r"/shipment_mgmt_test\1", _BASE_URL)

test_engine = create_engine(TEST_DB_URL, poolclass=NullPool)
TestSession = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def db():
    """每个测试一个连接 + 外层事务，测试结束后回滚。"""
    conn = test_engine.connect()
    tx = conn.begin()
    session = TestSession(bind=conn)
    # 把 session 的连接绑定到外层事务
    session.begin_nested()

    @pytest.fixture
    def _sync():
        pass

    yield session
    session.close()
    tx.rollback()
    conn.close()


@pytest.fixture
def client(db, monkeypatch):
    """TestClient，其 get_db 覆盖为测试 session（不提交，随 db fixture 回滚）。"""
    from app.db.session import get_db

    def _override():
        # 测试共享外层事务；失败的请求不回滚（fixture 结束时统一回滚）
        yield db
        db.flush()

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db):
    from app.models import User

    u = User(phone="13800000001", username="管理员", authority="admin",
             is_active=True, status=0, operator=None)
    db.add(u)
    db.flush()
    return u


@pytest.fixture
def normal_user(db, admin_user):
    from app.models import User

    u = User(phone="13900000002", username="普通用户", authority="normal",
             is_active=True, status=0, operator=admin_user.phone)
    db.add(u)
    db.flush()
    return u


@pytest.fixture
def admin_headers(admin_user):
    return {"Authorization": f"Bearer {create_token(admin_user.phone)}"}


@pytest.fixture
def normal_headers(normal_user):
    return {"Authorization": f"Bearer {create_token(normal_user.phone)}"}


@pytest.fixture
def seeded_options(db):
    from app.models import (
        BranchOption,
        ChargeCode,
        Creditor,
        Currency,
        Debtor,
        Department,
    )

    rows = []
    for m, codes in [
        (ChargeCode, ["DHLF", "OCUC", "OINSUR"]),
        (Currency, ["USD", "CNY", "EUR", "HKD"]),
        (Department, ["FIS", "FES", "FIA", "FEA"]),
        (Creditor, ["CNSHL", "MAERSK", "中远海运物流"]),
        (Debtor, ["CNSHO", "中远海运集运", "其它客户"]),
    ]:
        for code in codes:
            o = m(code=code, name=None, is_active=True, status=0,
                  operator="13800000001")
            db.add(o)
            rows.append(o)
    for code in ["SHL", "SHO"]:
        o = BranchOption(code=code, name=None, is_active=True, status=0,
                         operator="13800000001")
        db.add(o)
        rows.append(o)
    db.flush()
    return rows


@pytest.fixture
def seeded_shipment(db, admin_user, seeded_options):
    from app.models import Shipment

    s = Shipment(shipment_num="SH-20261119-0007", lifecycle="draft",
                 status=0, operator=admin_user.phone)
    db.add(s)
    db.flush()
    return s


@pytest.fixture
def seeded_charge(db, admin_user, seeded_shipment):
    from app.models import ChargeInfo

    c = ChargeInfo(
        shipment_id=seeded_shipment.id, job_num=seeded_shipment.shipment_num,
        charge_code="DHLF", department="FIS", branch="SHL",
        cost_currency="USD", os_cost_amt=8600, creditor="CNSHL",
        sell_currency="CNY", os_sell_amt=61400, debtor="CNSHO",
        status=0, operator=admin_user.phone,
    )
    db.add(c)
    db.flush()
    return c
