#!/usr/bin/env bash
# 一键部署（裸机路线：nginx 托管前端静态文件 + systemd 托管后端）
#
# 做的事：拉代码 → 装依赖 → 应用数据库迁移 → 构建前端 → 发布静态文件
#         → 重启后端 → 重载 nginx → 健康检查
#
# 用法：
#   sudo deploy/deploy.sh                 # 部署 main 分支的最新版
#   sudo deploy/deploy.sh --ref v0.3.0    # 部署指定 tag/分支
#   sudo deploy/deploy.sh --skip-build    # 只改后端时，跳过前端构建
#   deploy/deploy.sh --dry-run            # 只打印要做什么，不真的执行
#
# 路径与路径里的服务名可用环境变量覆盖：
#   APP_DIR=/srv/poManagementSystem WEB_ROOT=/var/www/poManagementSystem \
#   SERVICE=poManagementSystem deploy/deploy.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/srv/poManagementSystem}"
WEB_ROOT="${WEB_ROOT:-/var/www/poManagementSystem}"
SERVICE="${SERVICE:-poManagementSystem}"
NGINX_BIN="${NGINX_BIN:-nginx}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
GIT_REF=""
SKIP_BUILD=0
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --ref) GIT_REF="${2:-}"; shift 2 ;;
    --skip-build) SKIP_BUILD=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "不认识的参数：$1" >&2; exit 2 ;;
  esac
done

step() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
run() {
  if [ "$DRY_RUN" = "1" ]; then
    printf '   [dry-run] %s\n' "$*"
  else
    "$@"
  fi
}
need() { command -v "$1" >/dev/null 2>&1 || { echo "缺少命令：$1" >&2; exit 1; }; }

need git
[ -d "$APP_DIR" ] || { echo "代码目录不存在：$APP_DIR" >&2; exit 1; }

step "拉取代码"
if [ -n "$GIT_REF" ]; then
  run git -C "$APP_DIR" fetch --tags origin
  run git -C "$APP_DIR" checkout "$GIT_REF"
else
  run git -C "$APP_DIR" pull --ff-only origin main
fi
run git -C "$APP_DIR" log --oneline -1

step "安装后端依赖"
[ -x "$APP_DIR/backend/.venv/bin/pip" ] || { echo "后端虚拟环境不存在：$APP_DIR/backend/.venv" >&2; exit 1; }
run "$APP_DIR/backend/.venv/bin/pip" install --disable-pip-version-check -r "$APP_DIR/backend/requirements.txt"

step "应用数据库迁移（先迁移，再重启后端：新代码依赖新列）"
if [ "$DRY_RUN" = "1" ]; then
  printf '   [dry-run] cd %s/backend && .venv/bin/alembic upgrade head\n' "$APP_DIR"
else
  ( cd "$APP_DIR/backend" && .venv/bin/alembic upgrade head )
fi

if [ "$SKIP_BUILD" = "1" ]; then
  step "跳过前端构建（--skip-build）"
else
  step "构建前端"
  if [ "$DRY_RUN" = "1" ]; then
    printf '   [dry-run] cd %s/frontend && npm ci && npm run build\n' "$APP_DIR"
  else
    need node
    need npm
    ( cd "$APP_DIR/frontend" && { [ -d node_modules ] || npm ci; } && npm run build )
  fi
fi

step "发布前端静态文件"
if [ "$DRY_RUN" = "1" ]; then
  printf '   [dry-run] rsync -a --delete %s/frontend/dist/ %s/\n' "$APP_DIR" "$WEB_ROOT"
else
  mkdir -p "$WEB_ROOT"
  run rsync -a --delete "$APP_DIR/frontend/dist/" "$WEB_ROOT/"
fi

step "重启后端"
run systemctl restart "$SERVICE"

step "重载 nginx"
run "$NGINX_BIN" -t
run systemctl reload nginx

step "健康检查"
if [ "$DRY_RUN" = "1" ]; then
  printf '   [dry-run] curl -fsS %s\n' "$HEALTH_URL"
  exit 0
fi
for i in $(seq 1 30); do
  if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
    echo "后端已就绪：$HEALTH_URL"
    exit 0
  fi
  sleep 1
done
echo "健康检查失败：$HEALTH_URL 没在 30 秒内就绪" >&2
echo "看日志：journalctl -u $SERVICE -n 50 --no-pager" >&2
exit 1
