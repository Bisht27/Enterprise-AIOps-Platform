from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

from app.api.v1.dashboard.schemas import (
    DashboardSummary,
    MonitoringHistoryResponse,
)

from app.api.v1.dashboard.service import (
    get_dashboard_summary,
    get_monitoring_history,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/summary",
    response_model=DashboardSummary,
    status_code=status.HTTP_200_OK,
    summary="Get Dashboard Summary",
    description="Returns dashboard statistics including assets, alerts, tickets, and average system resource usage.",
)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_dashboard_summary(db)


@router.get(
    "/history/{asset_id}",
    response_model=MonitoringHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Monitoring History",
    description="Returns monitoring history for a specific asset.",
)
def monitoring_history(
    asset_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_monitoring_history(
        db=db,
        asset_id=asset_id,
        limit=limit,
    )