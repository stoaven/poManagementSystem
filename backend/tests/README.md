# 测试说明

测试库 `shipment_mgmt_test` 与应用共用同一套连接配置，只换库名。

默认从 `app.core.config` 的 `DATABASE_URL` 派生，因此**凭据与开发环境一致**——
改了 `.env` 里的口令，测试自动跟着变。

若本机 MySQL 的 root 口令与应用配置不同，用环境变量覆盖：

```bash
TEST_DATABASE_URL="mysql+pymysql://root@127.0.0.1:3306/shipment_mgmt_test?charset=utf8mb4" \
  .venv/bin/pytest tests/ -q
```

跑测试前需要本机 MySQL 已启动，并存在 `shipment_mgmt_test` 库（首次运行会自动建表）。
