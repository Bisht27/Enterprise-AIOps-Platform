from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ==========================================================
# Notification (in-app)
# ==========================================================

class NotificationResponse(BaseModel):
    id: int
    event_type: str
    severity: str
    title: str
    message: str

    asset_id: Optional[int] = None
    alert_id: Optional[int] = None
    ticket_id: Optional[int] = None

    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    unread_count: int


# ==========================================================
# Preferences
# ==========================================================

class NotificationPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    slack_enabled: Optional[bool] = None
    teams_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None

    critical_alerts: Optional[bool] = None
    warning_alerts: Optional[bool] = None
    offline_alerts: Optional[bool] = None
    ticket_notifications: Optional[bool] = None
    maintenance_alerts: Optional[bool] = None
    security_alerts: Optional[bool] = None
    daily_summary: Optional[bool] = None
    weekly_summary: Optional[bool] = None

    whatsapp_number: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    teams_webhook_url: Optional[str] = None
    sms_number: Optional[str] = None


class NotificationPreferenceResponse(BaseModel):
    user_id: int

    email_enabled: bool
    whatsapp_enabled: bool
    in_app_enabled: bool
    slack_enabled: bool
    teams_enabled: bool
    sms_enabled: bool

    critical_alerts: bool
    warning_alerts: bool
    offline_alerts: bool
    ticket_notifications: bool
    maintenance_alerts: bool
    security_alerts: bool
    daily_summary: bool
    weekly_summary: bool

    whatsapp_number: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    teams_webhook_url: Optional[str] = None
    sms_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Delivery history / retry / test
# ==========================================================

class DeliveryResponse(BaseModel):
    id: int
    notification_id: int
    channel: str
    recipient: str
    status: str
    provider: Optional[str] = None
    error: Optional[str] = None
    latency_ms: Optional[int] = None
    retry_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestEmailRequest(BaseModel):
    to_email: str


class TestWhatsAppRequest(BaseModel):
    to_number: str


class TestSlackRequest(BaseModel):
    webhook_url: str


class TestTeamsRequest(BaseModel):
    webhook_url: str


class TestSmsRequest(BaseModel):
    to_number: str


class RetryDeliveryRequest(BaseModel):
    delivery_id: int
