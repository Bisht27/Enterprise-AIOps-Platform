from pydantic import BaseModel
from datetime import datetime
from pydantic import BaseModel


class MonitoringHistoryItem(BaseModel):
    created_at: datetime
    cpu_usage: float
    ram_usage: float
    disk_usage: float
    network_sent: float
    network_received: float

    model_config = {
        "from_attributes": True
    }


class MonitoringHistoryResponse(BaseModel):
    asset_id: int
    history: list[MonitoringHistoryItem]

class DashboardSummary(BaseModel):
    total_assets: int

    online_assets: int

    offline_assets: int

    total_alerts: int

    open_alerts: int

    critical_alerts: int

    total_tickets: int

    open_tickets: int

    cpu_average: float

    ram_average: float

    disk_average: float