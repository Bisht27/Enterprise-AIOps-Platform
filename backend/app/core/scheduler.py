"""
The one background scheduler for everything that needs to run on a
cadence rather than in response to a request:

  - detect_offline_assets   -- every OFFLINE_CHECK_INTERVAL_MINUTES
  - check_expiry_reminders  -- once a day (warranty/license/maintenance)
  - send_daily_summary      -- once a day
  - send_weekly_summary     -- once a week
  - run_scheduled_reports   -- every 15 minutes (checks due schedules)
  - check_system_health     -- every 5 minutes (DB connectivity)

Uses APScheduler's BackgroundScheduler (thread-based) rather than an
async scheduler, since the rest of this codebase is a synchronous
SQLAlchemy app -- no event loop to hook into cleanly. Each job opens
its own DB session and closes it when done, same pattern as the
notification background-task dispatchers.

Started from app.main's startup event, stopped on shutdown.
"""

import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text

from app.core.config import settings
from app.core.security import decrypt_value
from app.database.session import SessionLocal
from app.models.asset import Asset
from app.models.user import User
from app.models.report import ScheduledReport
from app.services.notification_service import notify
from app.services.email_service import email_service
from app.services import report_analytics as analytics
try:
    from app.services import report_export as export_service
except Exception as e:
    print(f"Reports disabled: {e}")
    export_service = None
from app.schemas.report import ReportFilters

logger = logging.getLogger("scheduler")

_scheduler: BackgroundScheduler | None = None

# In-memory only -- resets on restart, which just means one spurious
# "back online" email after a redeploy that happened to catch a real
# outage. Acceptable trade-off for not needing a dedicated table for
# something this coarse-grained.
_db_was_down = False

REMINDER_WINDOWS_DAYS = {30, 14, 7, 1}


# ==========================================================
# Offline detection
# ==========================================================

def detect_offline_assets():
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(minutes=settings.OFFLINE_THRESHOLD_MINUTES)
        stale_assets = (
            db.query(Asset)
            .filter(Asset.is_online.is_(True), Asset.last_seen < cutoff)
            .all()
        )

        for asset in stale_assets:
            asset.is_online = False
            db.commit()

            notify(
                db, None,
                event_type="server_offline",
                title=f"Server Offline: {asset.asset_name}",
                message=f"{asset.asset_name} hasn't reported in for over {settings.OFFLINE_THRESHOLD_MINUTES} minutes.",
                severity="Critical",
                asset_id=asset.id,
                extra_fields=[
                    {"label": "Asset", "value": asset.asset_name},
                    {"label": "Hostname", "value": asset.hostname or "N/A"},
                    {"label": "Last Seen", "value": asset.last_seen.strftime("%Y-%m-%d %H:%M") if asset.last_seen else "Unknown"},
                ],
                dashboard_path=f"/asset/{asset.id}",
            )
    except Exception:  # noqa: BLE001
        logger.exception("detect_offline_assets job failed")
    finally:
        db.close()


# ==========================================================
# Expiry / maintenance reminders
# ==========================================================

def check_expiry_reminders():
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        assets = db.query(Asset).all()

        for asset in assets:
            _maybe_remind(db, asset, asset.warranty_expiry, today, "warranty_expiry_reminder", "Warranty")
            _maybe_remind(db, asset, asset.license_expiry, today, "license_expiry_reminder", "License")
            _maybe_remind(db, asset, asset.next_maintenance_date, today, "maintenance_reminder", "Maintenance")
    except Exception:  # noqa: BLE001
        logger.exception("check_expiry_reminders job failed")
    finally:
        db.close()


def _maybe_remind(db, asset, target_date, today, event_type, label):
    if not target_date:
        return

    days_remaining = (target_date.date() - today).days
    if days_remaining not in REMINDER_WINDOWS_DAYS:
        return

    notify(
        db, None,
        event_type=event_type,
        title=f"{label} Expiry Reminder: {asset.asset_name}",
        message=f"{label} for {asset.asset_name} expires in {days_remaining} day(s) ({target_date.strftime('%Y-%m-%d')}).",
        severity="Warning",
        asset_id=asset.id,
        extra_fields=[
            {"label": "Asset", "value": asset.asset_name},
            {"label": label, "value": target_date.strftime("%Y-%m-%d")},
            {"label": "Days Remaining", "value": str(days_remaining)},
        ],
        dashboard_path=f"/asset/{asset.id}",
    )


# ==========================================================
# Daily / weekly summaries
# ==========================================================

def _send_summary(period_label: str, preference_field: str):
    db = SessionLocal()
    try:
        dashboard = analytics.get_dashboard_report(db, ReportFilters())

        summary_lines = [
            {"label": "Total Assets", "value": str(dashboard["total_assets"])},
            {"label": "Online Assets", "value": str(dashboard["online_assets"])},
            {"label": "Critical Alerts", "value": str(dashboard["critical_alerts"])},
            {"label": "Open Tickets", "value": str(dashboard["open_tickets"])},
            {"label": "Avg CPU Usage", "value": f"{dashboard['avg_cpu_usage']}%"},
            {"label": "Availability", "value": f"{dashboard['asset_availability_pct']}%"},
        ]

        for user in db.query(User).filter(User.is_active.is_(True)).all():
            from app.services.notification_service import get_or_create_preference
            pref = get_or_create_preference(db, user.id)
            if not (pref.email_enabled and getattr(pref, preference_field, False) and user.email):
                continue

            email_service.send(
                to_email=user.email,
                subject=f"AIOps Platform - {period_label} Summary",
                title=f"{period_label} Summary",
                message=f"Here's your {period_label.lower()} platform summary.",
                severity="Info",
                fields=summary_lines,
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                dashboard_url=f"{settings.FRONTEND_URL}/reports",
            )
    except Exception:  # noqa: BLE001
        logger.exception("%s summary job failed", period_label)
    finally:
        db.close()


def send_daily_summary():
    _send_summary("Daily", "daily_summary")


def send_weekly_summary():
    _send_summary("Weekly", "weekly_summary")


# ==========================================================
# Scheduled report execution
# ==========================================================

_FREQUENCY_DELTA = {
    "Daily": timedelta(days=1),
    "Weekly": timedelta(weeks=1),
    "Monthly": timedelta(days=30),
    "Quarterly": timedelta(days=90),
    "Yearly": timedelta(days=365),
}


def run_scheduled_reports():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        due = (
            db.query(ScheduledReport)
            .filter(ScheduledReport.is_active.is_(True))
            .all()
        )

        for scheduled in due:
            next_run = scheduled.next_run_at or scheduled.created_at
            if next_run > now:
                continue

            _execute_scheduled_report(db, scheduled)

            scheduled.last_run_at = now
            delta = _FREQUENCY_DELTA.get(scheduled.frequency, timedelta(days=1))
            scheduled.next_run_at = now + delta
            db.commit()
    except Exception:  # noqa: BLE001
        logger.exception("run_scheduled_reports job failed")
    finally:
        db.close()


def _execute_scheduled_report(db, scheduled: ScheduledReport):
    filters = ReportFilters()
    if scheduled.filters_json:
        try:
            filters = ReportFilters.model_validate_json(scheduled.filters_json)
        except Exception:  # noqa: BLE001
            pass

    fmt = scheduled.export_format
    if fmt == "xlsx":
        content = export_service.to_excel_workbook(db, filters)
    else:
        data = analytics.get_dashboard_report(db, filters) if scheduled.report_type == "dashboard" \
            else _get_report_data(db, scheduled.report_type, filters)
        if fmt == "csv":
            content = export_service.to_csv(scheduled.report_type, data)
        elif fmt == "json":
            content = export_service.to_json(data)
        else:
            content = export_service.to_pdf(scheduled.report_type, data)

    file_name = f"{scheduled.report_type}_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{fmt}"

    if scheduled.delivery_email and scheduled.recipients:
        recipients = decrypt_value(scheduled.recipients)
        for email in [r.strip() for r in recipients.split(",") if r.strip()]:
            _send_report_email(email, scheduled.name, file_name, content, fmt)

    if scheduled.delivery_in_app and scheduled.created_by:
        creator = db.query(User).filter(User.id == scheduled.created_by).first()
        if creator:
            notify(
                db, None,
                event_type="scheduled_report_ready",
                title=f"Scheduled Report Ready: {scheduled.name}",
                message=f"Your scheduled '{scheduled.report_type}' report ({scheduled.frequency}) has been generated.",
                severity="Info",
                users=[creator],
                extra_fields=[{"label": "Report", "value": scheduled.name}, {"label": "Format", "value": fmt.upper()}],
                dashboard_path="/reports",
            )


def _get_report_data(db, report_type: str, filters: ReportFilters) -> dict:
    from app.api.v1.reports.service import REPORT_FUNCTIONS
    fn = REPORT_FUNCTIONS.get(report_type, analytics.get_dashboard_report)
    return fn(db, filters)


def _send_report_email(to_email: str, report_name: str, file_name: str, content: bytes, fmt: str):
    # Scheduled reports are delivered as an attachment -- EmailService's
    # HTML-only `send()` doesn't support attachments, so this builds a
    # small dedicated MIME message directly rather than stretching that
    # method's interface for one caller.
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.application import MIMEApplication

    if not email_service.is_configured():
        logger.warning("Skipping scheduled report email to %s -- SMTP not configured", to_email)
        return

    msg = MIMEMultipart()
    msg["Subject"] = f"Scheduled Report: {report_name}"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(f"Your scheduled report '{report_name}' is attached.", "plain"))

    attachment = MIMEApplication(content, Name=file_name)
    attachment["Content-Disposition"] = f'attachment; filename="{file_name}"'
    msg.attach(attachment)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.NOTIFICATION_TIMEOUT_SECONDS) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send scheduled report email to %s", to_email)


# ==========================================================
# System health (DB connectivity)
# ==========================================================

def check_system_health():
    global _db_was_down

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        if _db_was_down:
            _alert_admins("Database Connection Restored", "The platform database is reachable again.", "Info")
            _db_was_down = False
    except Exception as exc:  # noqa: BLE001
        logger.error("Database health check failed: %s", exc)
        if not _db_was_down:
            _alert_admins("Database Down", f"The platform database is unreachable: {exc}", "Critical")
        _db_was_down = True
    finally:
        try:
            db.close()
        except Exception:  # noqa: BLE001
            pass


def _alert_admins(title: str, message: str, severity: str):
    """
    DB-independent alert path -- used when the DB itself might be the
    thing that's down, so we can't go through notify()/NotificationDelivery
    (which need to write to that same DB). Emails ADMIN_ALERT_EMAILS
    directly instead.
    """
    recipients = [e.strip() for e in settings.ADMIN_ALERT_EMAILS.split(",") if e.strip()]
    if not recipients:
        logger.warning("%s (no ADMIN_ALERT_EMAILS configured to notify)", title)
        return

    for email in recipients:
        email_service.send(
            to_email=email,
            subject=f"AIOps Platform - {title}",
            title=title,
            message=message,
            severity=severity,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        )


# ==========================================================
# Lifecycle
# ==========================================================

def start_scheduler():
    global _scheduler
    if not settings.SCHEDULER_ENABLED or _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(timezone="UTC")

    _scheduler.add_job(
        detect_offline_assets, IntervalTrigger(minutes=5),
        id="detect_offline_assets", replace_existing=True,
    )
    _scheduler.add_job(
        check_system_health, IntervalTrigger(minutes=5),
        id="check_system_health", replace_existing=True,
    )
    _scheduler.add_job(
        run_scheduled_reports, IntervalTrigger(minutes=15),
        id="run_scheduled_reports", replace_existing=True,
    )
    _scheduler.add_job(
        check_expiry_reminders, CronTrigger(hour=8, minute=0),
        id="check_expiry_reminders", replace_existing=True,
    )
    _scheduler.add_job(
        send_daily_summary, CronTrigger(hour=7, minute=0),
        id="send_daily_summary", replace_existing=True,
    )
    _scheduler.add_job(
        send_weekly_summary, CronTrigger(day_of_week="mon", hour=7, minute=30),
        id="send_weekly_summary", replace_existing=True,
    )

    _scheduler.start()
    logger.info("Background scheduler started.")


def stop_scheduler():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Background scheduler stopped.")
