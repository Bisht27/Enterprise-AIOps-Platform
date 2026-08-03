from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.asset import Asset
from app.schemas.ml import (
    AnomalyResponse,
    ForecastResponse,
    HealthScoreResponse,
)
from app.api.v1.ml.service import (
    detect_anomalies,
    forecast_usage,
    compute_health_score,
)

router = APIRouter(
    prefix="/ml",
    tags=["Machine Learning"],
)


def _get_asset_or_404(db: Session, asset_id: int) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.get(
    "/assets/{asset_id}/anomalies",
    response_model=AnomalyResponse,
)
def get_asset_anomalies(
    asset_id: int,
    db: Session = Depends(get_db),
):
    _get_asset_or_404(db, asset_id)
    return detect_anomalies(db, asset_id)


@router.get(
    "/assets/{asset_id}/forecast",
    response_model=ForecastResponse,
)
def get_asset_forecast(
    asset_id: int,
    horizon: int = Query(
        default=5,
        ge=1,
        le=50,
        description="Number of future data points to predict",
    ),
    db: Session = Depends(get_db),
):
    _get_asset_or_404(db, asset_id)
    return forecast_usage(db, asset_id, horizon)


@router.get(
    "/assets/{asset_id}/health-score",
    response_model=HealthScoreResponse,
)
def get_asset_health_score(
    asset_id: int,
    db: Session = Depends(get_db),
):
    _get_asset_or_404(db, asset_id)
    return compute_health_score(db, asset_id)
