from datetime import datetime

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_assets: int
    online_assets: int
    offline_assets: int
    total_alerts: int
    open_alerts: int
    critical_alerts: int
    total_tickets: int
    open_tickets: int


class LiveMonitoringResponse(BaseModel):
    asset_id: int
    hostname: str
    cpu_usage: float
    ram_usage: float
    disk_usage: float
    network_sent: float
    network_received: float
    uptime: float
    last_seen: datetime