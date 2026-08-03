"""
NotificationService -- the single entry point every other module
(alerts, tickets, assets, agents, monitoring...) calls to fan a
business event out to in-app / email / WhatsApp.

How to wire a new event (e.g. from the monitoring module):

    from fastapi import BackgroundTasks
    from app.services.notification_service import notify

    def check_cpu(db, asset, background_tasks: BackgroundTasks):
        if asset.cpu_usage > 90:
            notify(
                db,
                background_tasks,
                event_type="critical_cpu_alert",
                title="Critical CPU Alert",
                message=f"CPU usage on {asset.asset_name} has exceeded 90%.",
                asset_id=asset.id,
                extra_fields=[
                    {"label": "Asset", "value": asset.asset_name},
                    {"label": "Hostname", "value": asset.hostname},
                    {"label": "CPU Usage", "value": f"{asset.cpu_usage}%"},
                ],
            )

That's it -- `notify()` handles preference filtering, template
rendering, and background delivery for every channel.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import SessionLocal
from app.models.notification import (
    Notification,
    NotificationDelivery,
    NotificationPreference,
)
from app.models.user import User
from app.services.notification_events import get_event
from app.services.email_service import email_service
from app.services.whatsapp import get_whatsapp_provider
from app.services.channels.slack_teams import send_slack_message, send_teams_message
from app.services.channels.sms import send_sms


# ==========================================================
# Preferences
# ==========================================================

def get_or_create_preference(db: Session, user_id: int) -> NotificationPreference:
    pref = (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == user_id)
        .first()
    )
    if pref:
        return pref

    pref = NotificationPreference(user_id=user_id)
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref


def _category_enabled(pref: NotificationPreference, category: str) -> bool:
    return bool(getattr(pref, category, True))


# ==========================================================
# Background dispatch (each opens its OWN db session -- the request's
# session is closed by the time a FastAPI BackgroundTask actually
# runs, so we can't reuse it here).
# ==========================================================

def _finish_delivery(db: Session, delivery: NotificationDelivery, result: dict) -> None:
    delivery.status = result.get("status", "Failed")
    delivery.provider = result.get("provider", delivery.provider)
    delivery.response = result.get("response")
    delivery.error = result.get("error")
    delivery.latency_ms = result.get("latency_ms")
    delivery.retry_count = result.get("retry_count", delivery.retry_count)
    delivery.updated_at = datetime.utcnow()
    db.commit()


def _send_email_delivery(delivery_id: int, title: str, message: str, severity: str,
                          fields: list[dict], dashboard_url: Optional[str]) -> None:
    db = SessionLocal()
    try:
        delivery = db.query(NotificationDelivery).filter(NotificationDelivery.id == delivery_id).first()
        if not delivery:
            return

        result = email_service.send(
            to_email=delivery.recipient,
            subject=title,
            title=title,
            message=message,
            severity=severity,
            fields=fields,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            dashboard_url=dashboard_url,
        )
        _finish_delivery(db, delivery, result)
    finally:
        db.close()


def _send_whatsapp_delivery(delivery_id: int, text_message: str) -> None:
    db = SessionLocal()
    try:
        delivery = db.query(NotificationDelivery).filter(NotificationDelivery.id == delivery_id).first()
        if not delivery:
            return

        provider = get_whatsapp_provider()
        result = provider.send(delivery.recipient, text_message)
        result.setdefault("provider", provider.name)
        _finish_delivery(db, delivery, result)
    finally:
        db.close()


def _send_slack_delivery(delivery_id: int, title: str, message: str) -> None:
    db = SessionLocal()
    try:
        delivery = db.query(NotificationDelivery).filter(NotificationDelivery.id == delivery_id).first()
        if not delivery:
            return
        result = send_slack_message(delivery.recipient, title, message)
        result.setdefault("provider", "slack")
        _finish_delivery(db, delivery, result)
    finally:
        db.close()


def _send_teams_delivery(delivery_id: int, title: str, message: str, severity: str) -> None:
    db = SessionLocal()
    try:
        delivery = db.query(NotificationDelivery).filter(NotificationDelivery.id == delivery_id).first()
        if not delivery:
            return
        result = send_teams_message(delivery.recipient, title, message, severity)
        result.setdefault("provider", "teams")
        _finish_delivery(db, delivery, result)
    finally:
        db.close()


def _send_sms_delivery(delivery_id: int, text_message: str) -> None:
    db = SessionLocal()
    try:
        delivery = db.query(NotificationDelivery).filter(NotificationDelivery.id == delivery_id).first()
        if not delivery:
            return
        result = send_sms(delivery.recipient, text_message)
        result.setdefault("provider", "twilio_sms")
        _finish_delivery(db, delivery, result)
    finally:
        db.close()


def _format_whatsapp_message(title: str, fields: list[dict], dashboard_url: Optional[str]) -> str:
    lines = [f"\U0001F6A8 {title}", ""]
    for f in fields:
        lines.append(f"{f['label']}:")
        lines.append(f"{f['value']}")
        lines.append("")
    lines.append(f"Time:\n{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
    if dashboard_url:
        lines.append("")
        lines.append(f"Open Dashboard:\n{dashboard_url}")
    return "\n".join(lines)


# ==========================================================
# Main entry point
# ==========================================================

def notify(
    db: Session,
    background_tasks,  # fastapi.BackgroundTasks | None
    event_type: str,
    title: str,
    message: str,
    severity: Optional[str] = None,
    asset_id: Optional[int] = None,
    alert_id: Optional[int] = None,
    ticket_id: Optional[int] = None,
    users: Optional[list[User]] = None,
    extra_fields: Optional[list[dict]] = None,
    dashboard_path: str = "/",
) -> list[Notification]:
    """
    Create in-app notifications and dispatch email/WhatsApp deliveries
    (respecting each user's NotificationPreference) for a business
    event. Safe to call with background_tasks=None (deliveries run
    synchronously instead -- used by the /notifications/retry and
    /notifications/test endpoints).
    """
    event_def = get_event(event_type)
    severity = severity or event_def.default_severity
    fields = extra_fields or []
    dashboard_url = f"{settings.FRONTEND_URL}{dashboard_path}"

    target_users = users if users is not None else (
        db.query(User).filter(User.is_active.is_(True)).all()
    )

    created: list[Notification] = []

    for user in target_users:
        pref = get_or_create_preference(db, user.id)

        if not _category_enabled(pref, event_def.category):
            continue

        notification = Notification(
            event_type=event_type,
            severity=severity,
            title=title,
            message=message,
            asset_id=asset_id,
            alert_id=alert_id,
            ticket_id=ticket_id,
            user_id=user.id,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        created.append(notification)

        if pref.in_app_enabled:
            db.add(NotificationDelivery(
                notification_id=notification.id,
                channel="in_app",
                recipient=user.username,
                status="Delivered",
                provider="in_app",
            ))
            db.commit()

        if pref.email_enabled and user.email:
            delivery = NotificationDelivery(
                notification_id=notification.id,
                channel="email",
                recipient=user.email,
                status="Pending",
                provider="smtp",
            )
            db.add(delivery)
            db.commit()
            db.refresh(delivery)

            args = (delivery.id, title, message, severity, fields, dashboard_url)
            if background_tasks is not None:
                background_tasks.add_task(_send_email_delivery, *args)
            else:
                _send_email_delivery(*args)

        if pref.whatsapp_enabled and pref.whatsapp_number:
            delivery = NotificationDelivery(
                notification_id=notification.id,
                channel="whatsapp",
                recipient=pref.whatsapp_number,
                status="Pending",
                provider=settings.WHATSAPP_PROVIDER,
            )
            db.add(delivery)
            db.commit()
            db.refresh(delivery)

            text_message = _format_whatsapp_message(title, fields, dashboard_url)
            if background_tasks is not None:
                background_tasks.add_task(_send_whatsapp_delivery, delivery.id, text_message)
            else:
                _send_whatsapp_delivery(delivery.id, text_message)

        if pref.slack_enabled and pref.slack_webhook_url:
            delivery = NotificationDelivery(
                notification_id=notification.id,
                channel="slack",
                recipient=pref.slack_webhook_url,
                status="Pending",
                provider="slack",
            )
            db.add(delivery)
            db.commit()
            db.refresh(delivery)

            if background_tasks is not None:
                background_tasks.add_task(_send_slack_delivery, delivery.id, title, message)
            else:
                _send_slack_delivery(delivery.id, title, message)

        if pref.teams_enabled and pref.teams_webhook_url:
            delivery = NotificationDelivery(
                notification_id=notification.id,
                channel="teams",
                recipient=pref.teams_webhook_url,
                status="Pending",
                provider="teams",
            )
            db.add(delivery)
            db.commit()
            db.refresh(delivery)

            if background_tasks is not None:
                background_tasks.add_task(_send_teams_delivery, delivery.id, title, message, severity)
            else:
                _send_teams_delivery(delivery.id, title, message, severity)

        if pref.sms_enabled and pref.sms_number:
            delivery = NotificationDelivery(
                notification_id=notification.id,
                channel="sms",
                recipient=pref.sms_number,
                status="Pending",
                provider="twilio_sms",
            )
            db.add(delivery)
            db.commit()
            db.refresh(delivery)

            # SMS has no formatting/length budget for the full
            # WhatsApp-style layout -- keep it to title + message.
            text_message = f"{title}\n{message}"
            if background_tasks is not None:
                background_tasks.add_task(_send_sms_delivery, delivery.id, text_message)
            else:
                _send_sms_delivery(delivery.id, text_message)

    return created
