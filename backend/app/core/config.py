from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # Public base URL of the frontend app. Used to build the URL encoded
    # inside each asset QR code (e.g. http://localhost:5173/asset/15).
    # Override in .env for production (e.g. https://my-domain.com).
    FRONTEND_URL: str = "http://localhost:5173"

    # ==========================================================
    # Email (SMTP) Notification Settings
    # ==========================================================
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "AIOps Platform <no-reply@aiops.local>"
    SMTP_TLS: bool = True

    # Max emails sent per rolling 60-second window (simple in-process
    # rate limiter -- see app/services/email_service.py).
    EMAIL_RATE_LIMIT_PER_MINUTE: int = 60

    # ==========================================================
    # WhatsApp Notification Settings
    # ==========================================================
    # One of: meta, twilio, gupshup, interakt
    WHATSAPP_PROVIDER: str = "meta"
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_NUMBER: str = ""
    # Override only if you need to hit a non-default API base (e.g. a
    # sandbox/staging endpoint). Left blank = provider's default.
    WHATSAPP_API_URL: str = ""

    # Twilio needs an Account SID in addition to the generic
    # WHATSAPP_TOKEN (used as the Auth Token for Twilio).
    TWILIO_ACCOUNT_SID: str = ""

    # Gupshup needs the source "app name" registered with them, in
    # addition to the generic WHATSAPP_TOKEN (used as the API key).
    GUPSHUP_APP_NAME: str = ""

    # ==========================================================
    # Additional Notification Channels (Slack / Teams / SMS)
    # ==========================================================
    # Slack/Teams deliver via a per-user incoming webhook URL (stored
    # on NotificationPreference, not here -- there's no single
    # platform-wide webhook). SMS reuses the Twilio credentials above.
    TWILIO_SMS_FROM_NUMBER: str = ""

    # ==========================================================
    # Notification Delivery Settings (shared by Email + WhatsApp)
    # ==========================================================
    NOTIFICATION_RETRY_COUNT: int = 3
    NOTIFICATION_TIMEOUT_SECONDS: int = 10

    # ==========================================================
    # Background Scheduler (reminders, summaries, scheduled reports,
    # offline detection, system health) -- see app/core/scheduler.py
    # ==========================================================
    SCHEDULER_ENABLED: bool = True
    # How often (in hours) an already-open, already-notified alert gets
    # a "still active" reminder notification. Read by
    # app/api/v1/alerts/service.py and app/api/v1/monitoring/service.py
    # instead of hardcoding the reminder window.
    ALERT_REMINDER_HOURS: float = 6
    # An agent that hasn't heartbeat-ed in this many minutes is
    # considered offline.
    OFFLINE_THRESHOLD_MINUTES: int = 10
    # Comma-separated email addresses that get direct, DB-independent
    # alerts (Database Down, etc.) -- see app/core/scheduler.py.
    ADMIN_ALERT_EMAILS: str = ""
    # Shared-secret header (X-System-Token) required by
    # POST /api/v1/system/report-failure, for external backup/uptime
    # scripts that don't have a user login.
    SYSTEM_WEBHOOK_TOKEN: str = ""

    class Config:
        env_file = ".env"


settings = Settings()