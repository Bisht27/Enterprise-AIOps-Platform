from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.init_db import init_db
from app.core.scheduler import start_scheduler, stop_scheduler

from app.api.v1.auth.router import router as auth_router
from app.api.v1.assets.router import router as asset_router
from app.api.v1.agents.router import router as agent_router
from app.api.v1.monitoring.router import router as monitoring_router
from app.api.v1.alerts.router import router as alerts_router
from app.api.v1.tickets.router import router as tickets_router
from app.api.v1.dashboard.router import router as dashboard_router
from app.api.v1.qr.router import router as qr_router
from app.api.v1.ml.router import router as ml_router
from app.api.v1.notifications.router import router as notifications_router
from app.api.v1.reports.router import router as reports_router
from app.api.v1.audit.router import router as audit_router
from app.api.v1.system.router import router as system_router

from app.websocket.router import router as websocket_router

app = FastAPI(
    title="AI Infrastructure Operations Platform",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    start_scheduler()


@app.on_event("shutdown")
def shutdown():
    stop_scheduler()


# -----------------------------
# API Routers
# -----------------------------

app.include_router(auth_router, prefix="/api/v1")
app.include_router(asset_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(qr_router, prefix="/api/v1")
app.include_router(ml_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")

# WebSocket
app.include_router(websocket_router)


@app.get("/")
def root():
    return {
        "message": "AI Infrastructure Operations Platform"
    }