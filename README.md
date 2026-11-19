# 货运订单费用管理

对内使用的货运订单收付款管理系统。前后端分离：Python/FastAPI 后端 + MySQL，Vue 3 单页应用前端。

一条**货运订单**（Shipment）下挂多条**费用信息**（Charge Info），每条费用信息同时承载一笔应付与一笔应收。

## 目录结构

```
poManagementSystem/
├── backend/            FastAPI 后端
│   ├── app/
│   │   ├── api/v1/     路由：auth / users / options / shipments / charge_infos
│   │   ├── core/       config、security（JWT）、deps（认证与权限依赖）
│   │   ├── db/         Base、审计字段 Mixin、session
│   │   ├── models/     SQLAlchemy 模型
│   │   ├── repositories/ 查询助手（status 过滤、筛选条件、选项校验）
│   │   └── cli.py      create-admin / seed-options
│   ├── alembic/        数据库迁移
│   └── tests/          pytest 测试
├── frontend/           Vue 3 + Element Plus 单页应用
├── prototype/          静态高保真原型（可直接打开 index.html 查看）
├── docker-compose.yml  本地 MySQL 8
└── openspec/           规格与变更文档
```

## 本地启动

### 1. 数据库

用 docker-compose 起 MySQL 8：

```bash
docker compose up -d
```

或者用本机已安装的 MySQL（需为 `root` 设置密码 `root` 以匹配默认配置）：

```bash
mysql -u root -e "CREATE DATABASE IF NOT EXISTS shipment_mgmt CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
```

### 2. 后端

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # 按需修改 DATABASE_URL 与 JWT_SECRET
.venv/bin/alembic upgrade head
.venv/bin/python -m app.cli create-admin --phone 13800000000 --username 管理员
.venv/bin/python -m app.cli seed-options
.venv/bin/uvicorn app.main:app --reload
```

服务起在 `http://localhost:8000`，健康检查 `GET /health`，接口文档 `http://localhost:8000/docs`。

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

开发期通过 Vite dev server 的 proxy 把 `/api` 转发到后端，无需额外配置跨域。

## 常用命令

| 命令 | 说明 |
|---|---|
| `backend/.venv/bin/pytest` | 跑后端测试 |
| `backend/.venv/bin/alembic revision --autogenerate -m "..."` | 生成迁移 |
| `backend/.venv/bin/alembic upgrade head` | 应用迁移 |
| `backend/.venv/bin/alembic downgrade -1` | 回退一版迁移 |
| `frontend/npm test` | 跑前端测试 |
| `frontend/npm run build` | 构建前端产物 |

## 权限模型

只有两级：`admin` 与 `normal`。

| 操作 | admin | normal |
|---|---|---|
| 六类选项的增删改与启停用 | 可 | 403 |
| 六类选项的候选列表读取 | 可 | 可 |
| 用户管理（列出、创建、修改、启停用、删除） | 可 | 403 |
| 货运订单与费用信息的增删改查 | 可 | 可 |

权限在每次请求时从数据库实时读取，因此调整权限或停用账号立即生效。

## 登录方式

以**手机号**登录，无密码无验证码——账号由管理员开通，手机号即唯一标识与登录凭证。
