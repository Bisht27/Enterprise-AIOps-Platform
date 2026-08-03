from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MonitoringCreate(BaseModel):
    asset_id: int

    cpu_usage: float

    ram_usage: float

    disk_usage: float

    network_sent: float

    network_received: float

    # Optional -- older agents won't send these; the consolidated
    # alert template shows "N/A" when absent.
    logged_in_user: Optional[str] = None

    running_processes: Optional[int] = None


class MonitoringResponse(MonitoringCreate):
    id: int

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)