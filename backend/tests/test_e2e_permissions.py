"""端到端冒烟：权限边界（design D26 / tasks 16.3）。"""
def _login(client, phone):
    r = client.post("/api/v1/auth/login", json={"phone": phone})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_normal_user_cannot_manage_options_or_users(client, db, admin_user,
                                                    normal_user, seeded_options):
    normal = _login(client, normal_user.phone)

    # 普通用户可以读候选列表
    r = client.get("/api/v1/options/candidates", headers=normal)
    assert r.status_code == 200

    # 选项写操作一律 403
    for method, path, body in [
        ("post", "/api/v1/options/departments", {"code": "FIS5"}),
        ("patch", "/api/v1/options/departments/1", {"code": "FIS"}),
        ("patch", "/api/v1/options/departments/1/status", {"is_active": False}),
        ("delete", "/api/v1/options/departments/1", None),
    ]:
        if body is None:
            r = getattr(client, method)(path, headers=normal)
        else:
            r = getattr(client, method)(path, headers=normal, json=body)
        assert r.status_code == 403, (path, r.status_code)

    # 用户管理一律 403
    for method, path, body in [
        ("get", "/api/v1/users", None),
        ("post", "/api/v1/users", {"phone": "13700000003", "username": "王磊",
                                   "authority": "normal"}),
        ("patch", "/api/v1/users/2", {"phone": "13900000002", "username": "普通用户",
                                      "authority": "admin"}),
        ("delete", "/api/v1/users/2", None),
    ]:
        if body is None:
            r = getattr(client, method)(path, headers=normal)
        else:
            r = getattr(client, method)(path, headers=normal, json=body)
        assert r.status_code == 403, (path, r.status_code)

    # 业务数据的增删改查不受权限限制
    sid = client.post("/api/v1/shipments", headers=normal,
                      json={"shipment_num": "SH-E2E-PERM"}).status_code
    assert sid == 201


def test_permission_change_takes_effect_immediately(client, db, admin_user,
                                                    normal_user, seeded_options):
    normal = _login(client, normal_user.phone)
    assert client.get("/api/v1/users", headers=normal).status_code == 403

    # 管理员把普通用户提为 admin
    admin = _login(client, admin_user.phone)
    r = client.patch(f"/api/v1/users/{normal_user.id}", headers=admin,
                     json={"phone": normal_user.phone, "username": "普通用户",
                           "authority": "admin"})
    assert r.status_code == 200, r.text

    # 同一个令牌立刻获得管理员权限（权限每次请求实时读库）
    assert client.get("/api/v1/users", headers=normal).status_code == 200


def test_disabled_account_cannot_use_existing_token(client, db, admin_user,
                                                   normal_user, seeded_options):
    normal = _login(client, normal_user.phone)
    admin = _login(client, admin_user.phone)

    assert client.get("/api/v1/auth/me", headers=normal).status_code == 200
    r = client.patch(f"/api/v1/users/{normal_user.id}/status", headers=admin,
                     json={"is_active": False})
    assert r.status_code == 200

    # 停用后旧令牌立即失效
    assert client.get("/api/v1/auth/me", headers=normal).status_code == 401
    assert client.post("/api/v1/auth/login",
                       json={"phone": normal_user.phone}).status_code == 401


def test_admin_cannot_disable_self(client, db, admin_user, seeded_options):
    admin = _login(client, admin_user.phone)
    r = client.patch(f"/api/v1/users/{admin_user.id}/status", headers=admin,
                     json={"is_active": False})
    assert r.status_code == 409
    assert "不能停用" in r.json()["detail"]
    db.refresh(admin_user)
    assert admin_user.is_active is True
