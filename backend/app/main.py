"""FastAPI 应用装配：路由注册、CORS、健康检查。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1 import auth, charge_infos, options, shipments, users

settings = get_settings()

app = FastAPI(title="货运订单费用管理", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(options.router, prefix="/api/v1")
app.include_router(shipments.router, prefix="/api/v1")
app.include_router(charge_infos.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"ok": True}
