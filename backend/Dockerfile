# 后端镜像：FastAPI + uvicorn（只装运行时依赖，不含测试依赖）
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 依赖单独一层：只改业务代码时不必重装依赖
COPY requirements.txt ./
RUN pip install -r requirements.txt

# 应用代码（含 alembic/ 与 alembic.ini，迁移在容器里也能跑）
COPY . .

# 非 root 运行
RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app

EXPOSE 8000

# 探活打的是应用自己的 /health
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"

# 迁移不在这里做：由 compose 的 migrate 服务先跑 alembic upgrade head，
# 否则多副本会同时抢着改表结构。
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
