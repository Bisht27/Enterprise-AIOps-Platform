from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AnomalyPoint(BaseModel):
    id: int
    created_at: datetime
    cpu_usage: float
    ram_usage: float
    disk_usage: float
    is_anomaly: bool
    anomaly_score: float


class AnomalyResponse(BaseModel):
    asset_id: int
    sample_size: int
    anomalies_found: int
    points: List[AnomalyPoint]
    message: Optional[str] = None


class ForecastPoint(BaseModel):
    step: int
    label: str
    predicted_cpu_usage: float
    predicted_ram_usage: float
    predicted_disk_usage: float


class ForecastResponse(BaseModel):
    asset_id: int
    sample_size: int
    horizon: int
    forecast: List[ForecastPoint]
    trend: dict
    message: Optional[str] = None


class HealthScoreResponse(BaseModel):
    asset_id: int
    health_score: float
    risk_level: str
    factors: dict
    message: Optional[str] = None
