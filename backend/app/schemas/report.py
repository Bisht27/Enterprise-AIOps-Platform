from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ==========================================================
# Dashboard summary
# ==========================================================

class CountBreakdown(BaseModel):
    label: str
    count: int


class ReportDashboardResponse(BaseModel):
    total_assets: int
    online_assets: int
    offline_assets: int
    healthy_assets: int
    critical_assets: int

    total_alerts: int
    critical_alerts: int
    warning_alerts: int

    open_tickets: int
    closed_tickets: int

    avg_cpu_usage: float
    avg_ram_usage: float
    avg_disk_usage: float
    asset_availability_pct: float

    monthly_incidents: int

    assets_by_type: list[CountBreakdown]
    assets_by_location: list[CountBreakdown]
    assets_by_os: list[CountBreakdown]
    assets_by_department: list[CountBreakdown]


# ==========================================================
# Filters (shared query params, documented here for the frontend)
# ==========================================================

class ReportFilters(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    asset_type: Optional[str] = None
    operating_system: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None
    asset_status: Optional[str] = None


# ==========================================================
# Scheduled reports
# ==========================================================

class ScheduledReportCreate(BaseModel):
    name: str
    report_type: str
    frequency: str
    cron_expression: Optional[str] = None
    export_format: str = "pdf"
    delivery_email: bool = True
    delivery_in_app: bool = False
    recipients: Optional[str] = None
    filters: Optional[ReportFilters] = None


class ScheduledReportResponse(BaseModel):
    id: int
    name: str
    report_type: str
    frequency: str
    cron_expression: Optional[str] = None
    export_format: str
    delivery_email: bool
    delivery_in_app: bool
    recipients: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ExportHistoryResponse(BaseModel):
    id: int
    report_type: str
    export_format: str
    file_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
