from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


# ==========================================================
# Design note
# ==========================================================
# The original spec asked for separate `EmailLog` / `WhatsAppLog` /
# `DeliveryHistory` / `NotificationQueue` tables. That's a lot of
# near-identical schemas (channel, status, response, error, retry
# count...) for what is really one concept: "an attempt to deliver a
# notification through a channel". To avoid duplicating that shape
# four times (and to respect SOLID / DRY), this module models it as a
# single `NotificationDelivery` table with a `channel` discriminator
# column ("email" / "whatsapp" / "in_app" / future "sms" / "slack").
#
# There's also no separate `NotificationQueue` table: because delivery
# is dispatched via FastAPI `BackgroundTasks` (in-process, not a
# persisted broker like Celery+Redis), the "queue" is really just
# `NotificationDelivery` rows sitting in `status="Pending"`. If this
# is later upgraded to Celery, that's the table a worker would poll.


class Notification(Base):
    """
    One notification "event" -- e.g. a Critical CPU Alert on a given
    asset. A single Notification can fan out to multiple channels
    (in-app, email, WhatsApp); each fan-out attempt is tracked as its
    own NotificationDelivery row.
    """

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    # One of the EVENT_TYPES in app/services/notification_events.py
    # e.g. "critical_cpu_alert", "ticket_created", "server_offline".
    event_type = Column(String(50), nullable=False, index=True)

    # "Critical" | "Warning" | "Info" -- drives email color + WhatsApp
    # emoji and lets preferences filter by category.
    severity = Column(String(20), default="Info")

    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Optional links back to the entity that triggered the event.
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)

    # Who this in-app notification belongs to.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    asset = relationship("Asset")
    alert = relationship("Alert")
    ticket = relationship("Ticket")

    deliveries = relationship(
        "NotificationDelivery",
        back_populates="notification",
        cascade="all, delete-orphan",
    )


class NotificationPreference(Base):
    """
    Per-user opt-in/opt-out for channels and event categories.
    One row per user (created lazily with defaults on first read).
    """

    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    # Channels
    email_enabled = Column(Boolean, default=True)
    whatsapp_enabled = Column(Boolean, default=False)
    in_app_enabled = Column(Boolean, default=True)
    slack_enabled = Column(Boolean, default=False)
    teams_enabled = Column(Boolean, default=False)
    sms_enabled = Column(Boolean, default=False)

    # Categories
    critical_alerts = Column(Boolean, default=True)
    warning_alerts = Column(Boolean, default=True)
    offline_alerts = Column(Boolean, default=True)
    ticket_notifications = Column(Boolean, default=True)
    maintenance_alerts = Column(Boolean, default=True)
    security_alerts = Column(Boolean, default=True)
    daily_summary = Column(Boolean, default=False)
    weekly_summary = Column(Boolean, default=False)

    # WhatsApp needs a destination number since it isn't derived from
    # the user's login email like SMTP is.
    whatsapp_number = Column(String(20), nullable=True)

    # Same idea for the newer channels -- Slack/Teams post via an
    # incoming webhook URL, SMS needs a phone number.
    slack_webhook_url = Column(String(300), nullable=True)
    teams_webhook_url = Column(String(300), nullable=True)
    sms_number = Column(String(20), nullable=True)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user = relationship("User")


class NotificationTemplate(Base):
    """
    Reusable, editable copy for each (event_type, channel) pair.
    Seeded with sensible defaults by the migration; admins can edit
    subject/body from the Settings page without a code change.
    """

    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)

    event_type = Column(String(50), nullable=False, index=True)
    channel = Column(String(20), nullable=False)  # email | whatsapp

    subject = Column(String(200), nullable=True)  # email only
    body_template = Column(Text, nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class NotificationDelivery(Base):
    """
    One delivery attempt of a Notification through one channel.
    This is the audit trail the "Delivery History" / "Retry" UI reads
    from, and doubles as the pending-work queue (status="Pending").
    """

    __tablename__ = "notification_deliveries"

    id = Column(Integer, primary_key=True, index=True)

    notification_id = Column(
        Integer,
        ForeignKey("notifications.id"),
        nullable=False,
    )

    channel = Column(String(20), nullable=False)  # email | whatsapp | in_app
    recipient = Column(String(150), nullable=False)  # email address / phone

    # Pending | Sent | Delivered | Failed | Retrying
    status = Column(String(20), default="Pending")

    provider = Column(String(50), nullable=True)  # e.g. "smtp", "meta"
    response = Column(Text, nullable=True)
    error = Column(Text, nullable=True)

    latency_ms = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    notification = relationship("Notification", back_populates="deliveries")
