from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User

from app.schemas.monitoring import (
    MonitoringCreate,
    MonitoringResponse,
)

from app.api.v1.monitoring.service import (
    save_metrics,
    get_latest_metrics,
    get_metrics_history,
    get_dashboard_metrics,
)

router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoring"],
)


# ==========================================================
# Agent Heartbeat
# ==========================================================

@router.post("/heartbeat", response_model=MonitoringResponse)
def heartbeat(
    data: MonitoringCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    return save_metrics(db, data, background_tasks)


# ==========================================================
# Latest Metrics of One Asset
# ==========================================================

@router.get("/latest/{asset_id}", response_model=MonitoringResponse)
def latest_metrics(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    monitoring = get_latest_metrics(db, asset_id)

    if not monitoring:
        raise HTTPException(
            status_code=404,
            detail="Monitoring data not found",
        )

    return monitoring


# ==========================================================
# Metrics History
# ==========================================================

@router.get(
    "/history/{asset_id}",
    response_model=List[MonitoringResponse],
)
def history(
    asset_id: int,
    range: Optional[str] = Query(
        default=None,
        description="Optional time filter: 1h, 24h, or 7d. Omit for full history.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_metrics_history(db, asset_id, range)


# ==========================================================
# Dashboard Summary
# ==========================================================

@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_dashboard_metrics(db)