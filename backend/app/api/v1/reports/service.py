from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import encrypt_value, decrypt_value
from app.models.report import ScheduledReport, ExportHistory
from app.schemas.report import ReportFilters, ScheduledReportCreate
from app.services import report_analytics as analytics
from app.services import report_export as export_service

_FREQUENCY_DELTA = {
    "Daily": timedelta(days=1),
    "Weekly": timedelta(weeks=1),
    "Monthly": timedelta(days=30),
    "Quarterly": timedelta(days=90),
    "Yearly": timedelta(days=365),
}

REPORT_FUNCTIONS = {
    "dashboard": analytics.get_dashboard_report,
    "asset": analytics.get_asset_report,
    "alert": analytics.get_alert_report,
    "ticket": analytics.get_ticket_report,
    "performance": analytics.get_performance_report,
    "security": analytics.get_security_report,
    "notification": analytics.get_notification_report,
    "compliance": analytics.get_compliance_report,
    "user_activity": analytics.get_user_activity_report,
}


def get_report(db: Session, report_type: str, filters: ReportFilters) -> dict:
    fn = REPORT_FUNCTIONS.get(report_type)
    if not fn:
        raise HTTPException(status_code=404, detail=f"Unknown report type: {report_type}")
    return fn(db, filters)


# ==========================================================
# Export
# ==========================================================

CONTENT_TYPES = {
    "csv": "text/csv",
    "json": "application/json",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


def export_report(
    db: Session,
    report_type: str,
    export_format: str,
    filters: ReportFilters,
    user_id: int | None = None,
) -> tuple[bytes, str, str]:
    export_format = export_format.lower()
    if export_format not in CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {export_format}")

    if export_format == "xlsx":
        content = export_service.to_excel_workbook(db, filters)
    else:
        data = get_report(db, report_type, filters)
        if export_format == "csv":
            content = export_service.to_csv(report_type, data)
        elif export_format == "json":
            content = export_service.to_json(data)
        else:  # pdf
            content = export_service.to_pdf(report_type, data)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_name = f"{report_type}_report_{timestamp}.{export_format}"

    db.add(ExportHistory(
        report_type=report_type,
        export_format=export_format,
        file_name=file_name,
        filters_json=filters.model_dump_json(),
        requested_by=user_id,
    ))
    db.commit()

    return content, file_name, CONTENT_TYPES[export_format]


def get_export_history(db: Session, limit: int = 50):
    return (
        db.query(ExportHistory)
        .order_by(ExportHistory.created_at.desc())
        .limit(limit)
        .all()
    )


# ==========================================================
# Scheduled reports
# ==========================================================
# Execution now happens in app/core/scheduler.py's run_scheduled_reports
# job (every 15 minutes, checks next_run_at). This module just owns
# the CRUD + the encrypt-at-rest handling for recipient emails.

def _schedule_to_dict(scheduled: ScheduledReport) -> dict:
    """
    Builds a plain dict for the API response with recipients
    decrypted -- deliberately NOT setting scheduled.recipients
    in-place, since that would mark the ORM attribute dirty and risk
    a later db.commit() in the same session persisting the plaintext
    back over the encrypted value.
    """
    return {
        "id": scheduled.id,
        "name": scheduled.name,
        "report_type": scheduled.report_type,
        "frequency": scheduled.frequency,
        "cron_expression": scheduled.cron_expression,
        "export_format": scheduled.export_format,
        "delivery_email": scheduled.delivery_email,
        "delivery_in_app": scheduled.delivery_in_app,
        "recipients": decrypt_value(scheduled.recipients) if scheduled.recipients else None,
        "is_active": scheduled.is_active,
        "created_at": scheduled.created_at,
        "last_run_at": scheduled.last_run_at,
        "next_run_at": scheduled.next_run_at,
    }


def create_scheduled_report(db: Session, data: ScheduledReportCreate, user_id: int | None):
    now = datetime.utcnow()
    scheduled = ScheduledReport(
        name=data.name,
        report_type=data.report_type,
        frequency=data.frequency,
        cron_expression=data.cron_expression,
        export_format=data.export_format,
        delivery_email=data.delivery_email,
        delivery_in_app=data.delivery_in_app,
        recipients=encrypt_value(data.recipients) if data.recipients else None,
        filters_json=data.filters.model_dump_json() if data.filters else None,
        created_by=user_id,
        next_run_at=now + _FREQUENCY_DELTA.get(data.frequency, timedelta(days=1)),
    )
    db.add(scheduled)
    db.commit()
    db.refresh(scheduled)
    return _schedule_to_dict(scheduled)


def list_scheduled_reports(db: Session):
    rows = db.query(ScheduledReport).order_by(ScheduledReport.created_at.desc()).all()
    return [_schedule_to_dict(r) for r in rows]


def delete_scheduled_report(db: Session, scheduled_id: int) -> bool:
    scheduled = db.query(ScheduledReport).filter(ScheduledReport.id == scheduled_id).first()
    if not scheduled:
        return False
    db.delete(scheduled)
    db.commit()
    return True
