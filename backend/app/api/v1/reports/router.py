from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user, require_admin
from app.models.user import User
from app.schemas.report import (
    ReportFilters,
    ScheduledReportCreate,
    ScheduledReportResponse,
    ExportHistoryResponse,
)
from app.api.v1.reports.service import (
    get_report,
    export_report,
    get_export_history,
    create_scheduled_report,
    list_scheduled_reports,
    delete_scheduled_report,
)
from app.services.audit import log_action

router = APIRouter(prefix="/reports", tags=["Reports"])


def _filters(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    asset_type: Optional[str] = None,
    operating_system: Optional[str] = None,
    location: Optional[str] = None,
    department: Optional[str] = None,
    severity: Optional[str] = None,
    priority: Optional[str] = None,
    asset_status: Optional[str] = None,
) -> ReportFilters:
    return ReportFilters(
        start_date=start_date,
        end_date=end_date,
        asset_type=asset_type,
        operating_system=operating_system,
        location=location,
        department=department,
        severity=severity,
        priority=priority,
        asset_status=asset_status,
    )


@router.get("/dashboard")
def dashboard_report(
    db: Session = Depends(get_db),
    filters: ReportFilters = Depends(_filters),
    current_user: User = Depends(get_current_user),
):
    return get_report(db, "dashboard", filters)


@router.get("/assets")
def asset_report(
    db: Session = Depends(get_db),
    filters: ReportFilters = Depends(_filters),
    current_user: User = Depends(get_current_user),
):
    return get_report(db, "asset", filters)


@router.get("/alerts")
def alert_report(
    db: Session = Depends(get_db),
    filters: ReportFilters = Depends(_filters),
    current_user: User = Depends(get_current_user),
):
    return get_report(db, "alert", filters)


@router.get("/tickets")
def ticket_report(
    db: Session = Depends(get_db),
    filters: ReportFilters = Depends(_filters),
    current_user: User = Depends(get_current_user),
):
    return get_report(db, "ticket", filters)


@router.get("/performance")
def performance_report(
    db: Session = Depends(get_db),
    filters: ReportFilters = Depends(_filters),
    current_user: User = Depends(get_current_user),
):
    return get_report(db, "performance", filters)


@router.get("/security")
def security_report(
    db: Session = Depends(get_db),
    filters: ReportFilters = Depends(_filters),
    current_user: User = Depends(get_current_user),
):
    return get_report(db, "security", filters)


@router.get("/notifications")
def notification_report(
    db: Session = Depends(get_db),
    filters: ReportFilters = Depends(_filters),
    current_user: User = Depends(get_current_user),
):
    return get_report(db, "notification", filters)


@router.get("/compliance")
def compliance_report(
    db: Session = Depends(get_db),
    filters: ReportFilters = Depends(_filters),
    current_user: User = Depends(get_current_user),
):
    return get_report(db, "compliance", filters)


@router.get("/user-activity")
def user_activity_report(
    db: Session = Depends(get_db),
    filters: ReportFilters = Depends(_filters),
    current_user: User = Depends(require_admin),
):
    return get_report(db, "user_activity", filters)


@router.get("/export")
def export(
    report_type: str = Query(..., description="dashboard | asset | alert | ticket | performance | security | notification | compliance | user_activity"),
    format: str = Query("pdf", description="pdf | xlsx | csv | json"),
    db: Session = Depends(get_db),
    filters: ReportFilters = Depends(_filters),
    current_user: User = Depends(get_current_user),
):
    content, file_name, content_type = export_report(
        db, report_type, format, filters, current_user.id
    )
    log_action(db, current_user.id, "report.export", target=file_name, detail=report_type)
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@router.get("/history", response_model=list[ExportHistoryResponse])
def export_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_export_history(db)


@router.post("/schedule", response_model=ScheduledReportResponse)
def schedule_report(
    data: ScheduledReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scheduled = create_scheduled_report(db, data, current_user.id)
    log_action(db, current_user.id, "report.schedule_create", target=data.name, detail=data.frequency)
    return scheduled


@router.get("/schedule", response_model=list[ScheduledReportResponse])
def list_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_scheduled_reports(db)


@router.delete("/schedule/{scheduled_id}")
def remove_schedule(
    scheduled_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    deleted = delete_scheduled_report(db, scheduled_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scheduled report not found")
    log_action(db, current_user.id, "report.schedule_delete", target=str(scheduled_id))
    return {"message": "Scheduled report deleted"}
