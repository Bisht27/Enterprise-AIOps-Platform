from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MetricCreate(BaseModel):
    asset_id: int
    cpu_usage: float
    ram_usage: float
    disk_usage: float
    network_sent: float
    network_received: float


class MetricResponse(MetricCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)