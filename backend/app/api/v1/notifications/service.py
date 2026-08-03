from datetime import datetime

from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
    NotificationDelivery,
    NotificationPreference,
)
from app.models.user import User
from app.schemas.notification import NotificationPreferenceUpdate
from app.services.notification_service import (
    get_or_create_preference,
    _send_email_delivery,
    _send_whatsapp_delivery,
    _format_whatsapp_message,
)
from app.services.email_service import email_service
from app.services.whatsapp import get_whatsapp_provider
from app.services.channels.slack_teams import send_slack_message, send_teams_message
from app.services.channels.sms import send_sms
from app.core.config import settings


# ==========================================================
# In-app notifications
# ==========================================================

def list_notifications(db: Session, user_id: int, limit: int = 50):
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )


def get_unread_count(db: Session, user_id: int) -> int:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
        .count()
    )


def mark_as_read(db: Session, user_id: int, notification_id: int):
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if not notification:
        return None

    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)
    return notification


# ==========================================================
# Delivery history / retry
# ==========================================================

def get_delivery_history(db: Session, user_id: int, limit: int = 100):
    return (
        db.query(NotificationDelivery)
        .join(Notification, Notification.id == NotificationDelivery.notification_id)
        .filter(Notification.user_id == user_id)
        .order_by(NotificationDelivery.created_at.desc())
        .limit(limit)
        .all()
    )


def retry_delivery(db: Session, delivery_id: int):
    """
    Re-attempts a Failed delivery synchronously (no BackgroundTasks
    here -- this endpoint's whole job is to report the outcome back
    to the caller immediately, e.g. for the "Retry" button in the UI).
    """
    delivery = db.query(NotificationDelivery).filter(NotificationDelivery.id == delivery_id).first()
    if not delivery:
        return None

    notification = db.query(Notification).filter(Notification.id == delivery.notification_id).first()

    delivery.status = "Retrying"
    delivery.retry_count = (delivery.retry_count or 0) + 1
    db.commit()

    if delivery.channel == "email":
        _send_email_delivery(
            delivery.id,
            notification.title,
            notification.message,
            notification.severity,
            [],
            f"{settings.FRONTEND_URL}/",
        )
    elif delivery.channel == "whatsapp":
        text_message = _format_whatsapp_message(notification.title, [], f"{settings.FRONTEND_URL}/")
        _send_whatsapp_delivery(delivery.id, text_message)

    db.refresh(delivery)
    return delivery


# ==========================================================
# Preferences
# ==========================================================

def get_preferences(db: Session, user_id: int) -> NotificationPreference:
    return get_or_create_preference(db, user_id)


def update_preferences(db: Session, user_id: int, data: NotificationPreferenceUpdate):
    pref = get_or_create_preference(db, user_id)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(pref, key, value)

    db.commit()
    db.refresh(pref)
    return pref


# ==========================================================
# Test send
# ==========================================================

def send_test_email(to_email: str) -> dict:
    return email_service.send(
        to_email=to_email,
        subject="Test Notification - AIOps Platform",
        title="Test Notification",
        message="This is a test email from your AIOps Platform notification settings.",
        severity="Info",
        fields=[{"label": "Sent At", "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M")}],
        timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        dashboard_url=f"{settings.FRONTEND_URL}/",
    )


def send_test_whatsapp(to_number: str) -> dict:
    provider = get_whatsapp_provider()

    message = _format_whatsapp_message(
        "Test Notification",
        [{"label": "Status", "value": "Your WhatsApp notifications are working"}],
        f"{settings.FRONTEND_URL}/",
    )

    print("Recipient:", to_number)
    print("Message:", message)

    result = provider.send(to_number, message)

    print("WhatsApp Result:", result)

    result.setdefault("provider", provider.name)
    return result


def send_test_slack(webhook_url: str) -> dict:
    return send_slack_message(
        webhook_url,
        "Test Notification",
        "This is a test message from your AIOps Platform notification settings.",
    )


def send_test_teams(webhook_url: str) -> dict:
    return send_teams_message(
        webhook_url,
        "Test Notification",
        "This is a test message from your AIOps Platform notification settings.",
        severity="Info",
    )


def send_test_sms(to_number: str) -> dict:
    return send_sms(
        to_number,
        "AIOps Platform: this is a test SMS from your notification settings.",
    )
