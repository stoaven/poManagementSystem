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
│   │   ├── schemas/    请求体与响应体模型（OpenAPI 契约的来源）
│   │   ├── repositories/ 查询助手（status 过滤、筛选条件、选项校验）
│   │   ├── services/   业务规则（成对写入、状态流转、批量导入、导出）
│   │   └── cli.py      create-admin / seed-options / export-openapi
│   ├── alembic/        数据库迁移
│   └── tests/          pytest 测试
├── frontend/           Vue 3 + Element Plus 单页应用
├── prototype/          静态高保真原型（可直接打开 index.html 查看）
├── docker-compose.yml  本地 MySQL 8
├── .github/workflows/  CI：pytest / vitest / 契约一致性
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

`seed-options` 会预置费用代码、应付部门、应付分支机构（`SHL`/`SHO`）、币种、
应付对象与应收对象六类初始选项。其中 `CNSHL` 与 `CNSHO` 互为对家，**两个表里
都得有** —— 新增费用信息时会按分支自动写入对方，缺一个创建就会被取值校验拒绝。

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
| `backend/.venv/bin/python -m app.cli export-openapi` | 导出 OpenAPI 契约到 `backend/openapi.json` |
| `frontend/npm test` | 跑前端测试 |
| `frontend/npm run build` | 构建前端产物（含 `vue-tsc` 类型检查） |
| `frontend/npm run generate:types` | 由 OpenAPI 契约重新生成前端类型 |

## 接口清单

全部接口以 `/api/v1` 为前缀。除标注外都需要 `Authorization: Bearer <令牌>`。

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/auth/login` | 公开 | 手机号登录换令牌（无密码无验证码） |
| GET | `/auth/me` | 登录 | 当前用户信息 |
| GET | `/users` | admin | 用户列表（可按关键字与权限级别筛选） |
| POST | `/users` | admin | 新建用户 |
| PATCH | `/users/{id}` | admin | 修改手机号、用户名称、权限级别 |
| PATCH | `/users/{id}/status` | admin | 启用/停用（不能停用自己） |
| DELETE | `/users/{id}` | admin | 软删除用户 |
| GET | `/options/candidates` | 登录 | 一次取回六类候选（录入下拉用） |
| GET | `/options/{kind}` | admin | 选项管理列表（**默认已过滤掉已软删除的项**，含已停用项，附被引用条数） |
| GET | `/options/{kind}/options` | 登录 | 候选列表（仅启用未删除，支持关键字过滤） |
| POST | `/options/{kind}` | admin | 新增选项 |
| PATCH | `/options/{kind}/{id}` | admin | 改名称（code 创建后不可修改） |
| PATCH | `/options/{kind}/{id}/status` | admin | 启用/停用 |
| GET | `/options/{kind}/{id}/references` | admin | 删除前的引用数量预检 |
| DELETE | `/options/{kind}/{id}` | admin | 软删除（返回删除前的引用数量） |
| POST | `/options/{kind}/import` | admin | 批量导入选项（上传 code/name 的 CSV，按 code upsert） |
| GET | `/shipments` | 登录 | 货运订单列表（分页 + 关键字 + 业务状态；**不返回任何金额**） |
| POST | `/shipments` | 登录 | 新建货运订单（单号全局唯一，不区分大小写） |
| GET | `/shipments/{id}` | 登录 | 订单详情：其下全部费用信息（不做金额合计） |
| GET | `/shipments/{id}/charge-infos/export` | 登录 | 导出该订单的费用信息为 Excel（**英文表头**） |
| PATCH | `/shipments/{id}` | 登录 | 修改货运订单号 |
| DELETE | `/shipments/{id}` | 登录 | 软删除订单 |
| POST | `/shipments/{id}/confirm\|complete\|cancel` | 登录 | 状态流转（草稿→确认/取消，已确认→完成/取消） |
| POST | `/shipments/{id}/charge-infos` | 登录 | 新增费用信息（**一次写入两条**，见下） |
| PATCH | `/charge-infos/{id}` | 登录 | 修改费用信息 |
| DELETE | `/charge-infos/{id}` | 登录 | 软删除费用信息 |

`{kind}` 只接受六类固定值：`charge_codes`、`departments`、`branches`、`currencies`、
`creditors`、`debtors`，其余一律 404。

## 新增费用信息会写入两条记录

页面填一条费用信息（九项），点保存后系统写入**两条**记录——A 记在填写的分支
机构上，B 记在镜像分支上：

| 字段 | A | B |
|---|---|---|
| 费用代码 / 应付部门 | 页面 | 同 A |
| 应付分支机构 | 页面 | 镜像分支（`SHL`↔`SHO`） |
| 应付币种 / 应付金额 | 页面 | 同 A 的应收币种与金额 |
| 应付对象 | 页面 | 对家单位（同 A 的应收对象：`SHL`→`CNSHO`，`SHO`→`CNSHL`） |
| 应收币种 / 应收金额 | 同 A 的应付币种与金额 | 页面 |
| 应收对象 | 对家单位（`SHL`→`CNSHO`，`SHO`→`CNSHL`） | 页面 |

两条在同一事务内写入，任一条不合法两条都不落库。分支机构只有 `SHL` 与 `SHO`
两种，填别的会被拒绝（没有对应的镜像分支，对家也无从确定）。

## 六类选项表

| kind | 表名 | 中文 | 初始数据 |
|---|---|---|---|
| `charge_codes` | `charge_codes` | 费用代码 | `DHLF` `OCUC` `OINSUR` |
| `departments` | `departments` | 应付部门 | `FIS` `FES` `FIA` `FEA` |
| `branches` | `branches` | 应付分支机构 | `SHL` `SHO` |
| `currencies` | `currencies` | 币种 | `USD` `CNY` `EUR` `HKD` |
| `creditors` | `creditors` | 应付对象 | `CNSHL` `CNSHO` `MAERSK` `中远海运物流` |
| `debtors` | `debtors` | 应收对象 | `CNSHO` `CNSHL` `中远海运集运` `其它客户` |

## 权限模型

只有两级：`admin` 与 `normal`。

| 操作 | admin | normal |
|---|---|---|
| 六类选项的增删改与启停用 | 可 | 403 |
| 六类选项的候选列表读取 | 可 | 可 |
| 用户管理（列出、创建、修改、启停用、删除） | 可 | 403 |
| 货运订单与费用信息的增删改查 | 可 | 可 |

权限在每次请求时从数据库实时读取，因此调整权限或停用账号立即生效。

## 批量导入选项

选项维护页有「批量导入」按钮，上传一份 CSV 即可批量写入**当前这一类**选项
（六类都支持）。CSV 要求：

- 表头两列：`code` 与 `name`（列序不限、大小写不敏感，UTF-8 编码，可带 BOM）
- 一行一个选项，`code` 不能为空

导入按 `code` **upsert**：已存在的 `code` 更新它的名称，不存在的 `code` 新增。
已软删除的 `code` 会被**跳过**（不复活），导入结果里会报告跳过了几条。
导入完页面会提示「新增 X 条，更新 Y 条」，有问题的行单独提示。

## 导出 Excel

货运订单详情页有「导出 Excel」按钮，把该订单下的**全部费用信息**导出成一个
`.xlsx` 文件。表头用**上游英文字段名**：

```
Job Num. | Charge Code | Department | Branch | Cost Currency |
OS Cost Amt | Creditor | Sell Currency | OS Sell Amt | Debtor
```

两列金额以**数值**写入（可直接在 Excel 里求和与筛选），已软删除的记录不导出。
文件名取自货运订单号，如 `charge-info-SSHL26309129.xlsx`。

## 登录方式

以**手机号**登录，无密码无验证码——账号由管理员开通，手机号即唯一标识与登录凭证。
