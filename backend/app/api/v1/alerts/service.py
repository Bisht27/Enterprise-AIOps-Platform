from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import Alert
from app.models.asset import Asset
from app.models.ticket import Ticket
from app.schemas.alert import AlertCreate
from app.services.notification_service import notify

# Reminder cadence for "still active" notifications, configurable via
# ALERT_REMINDER_HOURS (see app/core/config.py) instead of a hardcoded
# constant, so ops can tune it per environment without a code change.
REMINDER_INTERVAL = timedelta(hours=settings.ALERT_REMINDER_HOURS)

_ALERT_TYPE_EVENT_MAP = {
    "cpu": "critical_cpu_alert",
    "ram": "critical_ram_alert",
    "memory": "high_memory_usage",
    "disk": "critical_disk_alert",
    "network": "high_network_usage",
    "security": "security_incident",
    "database": "database_down",
    "application": "application_down",
    "backup": "backup_failed",
    "health": "health_status_changed",
}


def _event_type_for_alert(alert_type: str):
    alert_type = alert_type.lower()

    for key, value in _ALERT_TYPE_EVENT_MAP.items():
        if key in alert_type:
            return value

    return "critical_alert"


def create_alert(db: Session, data: AlertCreate, background_tasks=None, notify_individually: bool = True):
    """
    Create only one OPEN alert for the same Asset + Alert Type.
    If the alert is already open, do not send duplicate notifications.
    Send a reminder only once every 24 hours.

    notify_individually=False is used by the monitoring threshold
    checker (app/api/v1/monitoring/service.py), which creates/updates
    several per-metric alerts (CPU/RAM/Disk/Network) in one cycle and
    then sends a single consolidated notification for all of them
    instead of one email/WhatsApp message per metric.
    """

    existing = (
        db.query(Alert)
        .filter(
            Alert.asset_id == data.asset_id,
            Alert.alert_type == data.alert_type,
            Alert.status == "Open",
        )
        .first()
    )

    now = datetime.now(timezone.utc)

    # =====================================================
    # Alert already exists
    # =====================================================
    if existing:

        # Update only if message or severity changed
        changed = False

        if existing.message != data.message:
            existing.message = data.message
            changed = True

        if existing.severity != data.severity:
            existing.severity = data.severity
            changed = True

        if changed:
            db.commit()
            db.refresh(existing)

        # Reminder only every 24 hours
        if existing.created_at:

            last = existing.created_at

            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)

            if notify_individually and (now - last) >= REMINDER_INTERVAL:

                asset = (
                    db.query(Asset)
                    .filter(Asset.id == existing.asset_id)
                    .first()
                )

                notify(
                    db=db,
                    background_tasks=background_tasks,
                    event_type=_event_type_for_alert(existing.alert_type),
                    title=f"{existing.alert_type} Still Active",
                    message=existing.message,
                    severity=existing.severity.capitalize(),
                    asset_id=existing.asset_id,
                    alert_id=existing.id,
                    dashboard_path=f"/asset/{existing.asset_id}",
                )

                # DON'T change created_at.
                # Use it only as a reminder reference.
                existing.last_notified_at = now.replace(tzinfo=None)
                db.commit()

        return existing

    # =====================================================
    # Create New Alert
    # =====================================================

    alert = Alert(**data.model_dump())

    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Auto-create ticket for Critical alerts
    if alert.severity.lower() == "critical":

        ticket = Ticket(
            alert_id=alert.id,
            title=f"{alert.alert_type} Alert",
            description=alert.message,
            priority="High",
            status="Open",
            assigned_to=None,
            resolution_notes=None,
        )

        db.add(ticket)
        db.commit()

    if notify_individually:
        notify(
            db=db,
            background_tasks=background_tasks,
            event_type=_event_type_for_alert(alert.alert_type),
            title=f"{alert.alert_type} Alert",
            message=alert.message,
            severity=alert.severity.capitalize(),
            asset_id=alert.asset_id,
            alert_id=alert.id,
            dashboard_path=f"/asset/{alert.asset_id}",
        )
        alert.last_notified_at = now.replace(tzinfo=None)
        db.commit()

    return alert
# =====================================================
# Get All Alerts
# =====================================================

def get_all_alerts(db: Session):
    return (
        db.query(Alert)
        .order_by(Alert.created_at.desc())
        .all()
    )


# =====================================================
# Get Single Alert
# =====================================================

def get_alert(db: Session, alert_id: int):
    return (
        db.query(Alert)
        .filter(Alert.id == alert_id)
        .first()
    )


# =====================================================
# Resolve Alert
# =====================================================

def resolve_alert(db: Session, alert_id: int):

    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id)
        .first()
    )

    if alert is None:
        return None

    alert.status = "Resolved"
    alert.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.commit()
    db.refresh(alert)

    return alert


# =====================================================
# Delete Alert
# =====================================================

def delete_alert(db: Session, alert_id: int):

    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id)
        .first()
    )

    if alert is None:
        return None

    db.delete(alert)
    db.commit()

    return True