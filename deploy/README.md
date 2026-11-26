# 部署

两条路线，任选其一：

- **裸机（nginx + systemd）**：服务器上装 MySQL、nginx、Python 3.11、Node 20，
  前端构建产物交给 nginx 托管，后端由 systemd 跑 uvicorn。适合已有运维环境的机器。
- **Docker（compose）**：MySQL、后端、前端 nginx 全在容器里，一条命令拉起来。
  适合机器上不想装 MySQL/Node 的情况。

两条路线都遵循同一个顺序：**先应用数据库迁移，再重启后端**——新代码会读写
`charge_info` 的新列，列不存在的话新增费用信息会直接报错。

---

## 一、裸机路线

### 1. 首次部署

```bash
# 代码
sudo git clone https://github.com/stoaven/poManagementSystem.git /srv/poManagementSystem
cd /srv/poManagementSystem

# 后端：虚拟环境 + 依赖
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
sudo cp .env.example .env && sudo nano .env     # 改 DATABASE_URL / JWT_SECRET / CORS_ORIGINS
sudo chown -R www-data:www-data /srv/poManagementSystem/backend/.env

# 数据库
cd ..
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS shipment_mgmt CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
cd backend && .venv/bin/alembic upgrade head

# 初始账号与选项数据（只在第一次；选项表已有数据就别重复 seed）
.venv/bin/python -m app.cli create-admin --phone 13800000000 --username 管理员
.venv/bin/python -m app.cli seed-options

# 前端构建
cd ../frontend && npm ci && npm run build
sudo mkdir -p /var/www/poManagementSystem
sudo rsync -a --delete frontend/dist/ /var/www/poManagementSystem/

# systemd + nginx
sudo cp deploy/poManagementSystem.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now poManagementSystem
sudo nano deploy/nginx.conf        # 改 server_name 与 root
sudo cp deploy/nginx.conf /etc/nginx/sites-available/poManagementSystem
sudo ln -s /etc/nginx/sites-available/poManagementSystem /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 2. 日常发版

```bash
sudo /srv/poManagementSystem/deploy/deploy.sh
```

脚本做的事：拉代码 → 装依赖 → `alembic upgrade head` → 构建前端 → 发布到
`/var/www/poManagementSystem` → 重启 systemd 服务 → 重载 nginx → 探活。

常用参数：

```bash
deploy/deploy.sh --ref v0.3.0     # 部署指定 tag（回滚到旧版本也用它）
deploy/deploy.sh --skip-build     # 只改后端时跳过前端构建
deploy/deploy.sh --dry-run        # 只打印步骤不执行
```

路径可以覆盖：`APP_DIR=... WEB_ROOT=... SERVICE=... deploy/deploy.sh`。

### 3. 首次部署之外还要改的

- `deploy/poManagementSystem.service` 里的 `WorkingDirectory` / `ExecStart` /
  `EnvironmentFile` 三处路径要改成你服务器上的实际路径（默认 `/srv/poManagementSystem`）。
- `deploy/nginx.conf` 里的 `server_name` 与 `root`。
- HTTPS：另配 443 的 server 块并签发证书（`certbot --nginx -d 你的域名`）。

---

## 二、Docker 路线

```bash
cp deploy/.env.prod.example deploy/.env.prod
nano deploy/.env.prod            # 改 MYSQL_ROOT_PASSWORD 与 JWT_SECRET

docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml up -d --build
```

服务与端口：

| 服务 | 说明 | 端口 |
|---|---|---|
| `frontend` | nginx，托管前端并反代 `/api` | 对外 80（`HTTP_PORT` 可改） |
| `backend` | FastAPI | 仅容器内 8000 |
| `migrate` | 一次性：`alembic upgrade head` | 无 |
| `db` | MySQL 8 | 不对外 |

发版：

```bash
git pull
docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml up -d --build
```

`migrate` 会在 `backend` 之前跑完迁移；迁移失败时 `backend` 不会启动。

看日志：

```bash
docker compose --env-file deploy/.env.prod -f deploy/docker-compose.prod.yml logs -f backend
```

---

## 三、这次改了什么（部署时要知道的）

| 变更 | 影响 |
|---|---|
| 迁移 `2f2ae1c94190`：`charge_codes.name` → `description`（**列改名**） | 不丢数据，513 条费用代码的描述保留 |
| 迁移 `3d8f1a6b42c7`：`charge_info` 新增 5 列 + 数据回填 | 加的是可空列；回填有两条 `UPDATE`，行数大时挑低峰期做 |
| 后端：成对写入、四个折算后金额、导出十四栏 | 需重启后端 |
| 前端：详情页表格、弹窗、下拉标签 | 需重新构建并替换静态文件 |

**回滚**：

- 只回退代码（推荐）：`deploy.sh --ref <上一个 tag>`，多余的列留着不写不影响。
- 连表结构一起回滚：`cd backend && .venv/bin/alembic downgrade 2f2ae1c94190`
  （会删掉新列，列里的新数据随之消失；`charge_codes` 的列名改回去，内容不丢）。
- 无论怎么回滚，**先备份数据库**：`mysqldump -u <user> -p <库名> > backup.sql`。

---

## 四、部署后自检

```bash
# 1. 后端活着
curl -s http://127.0.0.1:8000/health          # {"ok":true}

# 2. 迁移到位
mysql -u <user> -p -e "SHOW COLUMNS FROM shipment_mgmt.charge_info" | tail -5
#    应能看到 description / estimated_cost / local_cost_amt /
#    estimated_revenue / local_sell_amt

# 3. 浏览器打开 http://<域名>/#/shipments/6
#    - 表格十四栏顺序对不对
#    - 新增费用信息：选费用代码后描述是否自动带出
#    - 导出 Excel：表头是不是那十四个英文名
```

## 五、文件说明

| 文件 | 用途 |
|---|---|
| `deploy/deploy.sh` | 裸机路线的一键部署脚本 |
| `deploy/nginx.conf` | 裸机路线的 nginx 站点配置 |
| `deploy/poManagementSystem.service` | 后端的 systemd 单元 |
| `deploy/docker-compose.prod.yml` | Docker 路线的四个服务 |
| `deploy/.env.prod.example` | Docker 路线的配置样例 |
| `backend/Dockerfile` | 后端镜像 |
| `frontend/Dockerfile` | 前端镜像（多阶段：构建 → nginx） |
| `frontend/nginx.conf` | 前端容器里的 nginx 配置 |
