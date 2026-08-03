from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_db, require_admin
from app.core.security import mask_secret
from app.models.user import User
from app.services.notification_service import notify

router = APIRouter(prefix="/system", tags=["System"])


class SystemFailureReport(BaseModel):
    # backup_failed | application_down
    event_type: str
    title: str
    message: str
    severity: str = "Critical"
    source: str | None = None  # e.g. "nightly-backup-cron", "uptime-checker"


def _verify_system_token(x_system_token: str | None = Header(default=None)):
    """
    External scripts (a backup cron job, an uptime monitor) don't have
    a user login, so this endpoint is protected by a shared secret
    header instead of JWT. Only enforced if SYSTEM_WEBHOOK_TOKEN is
    actually set -- if it's blank (default), the endpoint is open,
    which is fine for local/dev use but should be set before exposing
    this publicly.
    """
    if settings.SYSTEM_WEBHOOK_TOKEN and x_system_token != settings.SYSTEM_WEBHOOK_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing X-System-Token header.")


@router.get("/config-status")
def config_status(current_user: User = Depends(require_admin)):
    """
    Read-only view of what's configured, for the Settings page.
    Never returns actual secret values -- only whether something is
    set, and a masked last-4-characters hint where that's useful.
    Since credentials live in .env (not the DB), this is the only
    "Settings" surface for them -- editing still means editing .env
    and restarting the app.
    """
    return {
        "email": {
            "configured": bool(settings.SMTP_HOST and settings.SMTP_USERNAME),
            "host": settings.SMTP_HOST or None,
            "username": mask_secret(settings.SMTP_USERNAME) if settings.SMTP_USERNAME else None,
            "from": settings.SMTP_FROM,
        },
        "whatsapp": {
            "provider": settings.WHATSAPP_PROVIDER,
            "configured": bool(settings.WHATSAPP_TOKEN),
            "business_number": settings.WHATSAPP_BUSINESS_NUMBER or None,
        },
        "sms": {
            "configured": bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_SMS_FROM_NUMBER),
            "from_number": settings.TWILIO_SMS_FROM_NUMBER or None,
        },
        "scheduler": {
            "enabled": settings.SCHEDULER_ENABLED,
            "offline_threshold_minutes": settings.OFFLINE_THRESHOLD_MINUTES,
        },
        "admin_alerts": {
            "configured": bool(settings.ADMIN_ALERT_EMAILS),
            "recipient_count": len([e for e in settings.ADMIN_ALERT_EMAILS.split(",") if e.strip()]),
        },
        "system_webhook": {
            "token_set": bool(settings.SYSTEM_WEBHOOK_TOKEN),
        },
        "retry_count": settings.NOTIFICATION_RETRY_COUNT,
        "notification_timeout_seconds": settings.NOTIFICATION_TIMEOUT_SECONDS,
    }


@router.get("/health")
def health(db: Session = Depends(get_db)):
    """
    Public-ish health check (no auth) -- returns DB connectivity
    status. Point an external uptime monitor at this; if it stops
    responding at all, that itself is your Application Down signal
    (a dead process can't self-report that it's dead).
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:  # noqa: BLE001
        db_status = f"error: {exc}"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/report-failure", dependencies=[Depends(_verify_system_token)])
def report_failure(
    data: SystemFailureReport,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    For external scripts to report a Backup Failed or Application Down
    event -- these can't be self-detected from inside this app (a
    failed backup job runs outside this process; a down application
    can't run its own code to report itself down). Point your backup
    script's failure handler or your uptime monitor's webhook here.
    """
    if data.event_type not in {"backup_failed", "application_down"}:
        raise HTTPException(
            status_code=400,
            detail="event_type must be 'backup_failed' or 'application_down'.",
        )

    notify(
        db, background_tasks,
        event_type=data.event_type,
        title=data.title,
        message=data.message,
        severity=data.severity,
        extra_fields=[{"label": "Source", "value": data.source or "external"}],
        dashboard_path="/",
    )
    return {"message": "Reported"}
