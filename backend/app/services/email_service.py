import logging
import smtplib
import time
from collections import deque
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger("notifications.email")

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"

# Root-cause note (Issue 1 -- duplicate/undeliverable emails):
# There is no hardcoded "admin@example.com" anywhere in this codebase.
# notify() only emails active Users with email_enabled=True, using
# whatever address is on their User row. If a placeholder/test address
# like admin@example.com is receiving mail, it's because a User record
# in the database actually has that email -- not a code bug. See the
# cleanup query in backend/app/utils/find_placeholder_emails.py.
#
# This guard is defense-in-depth on top of that: known placeholder /
# non-routable domains are rejected here so a stray test account can
# never actually generate an SMTP attempt (and the resulting "Address
# not found" bounce), even before the underlying User row is cleaned up.
PLACEHOLDER_EMAIL_DOMAINS = {
    "example.com", "example.org", "example.net",
    "test.com", "sample.com", "domain.com",
    "localhost", "invalid",
}


def is_placeholder_email(email: str) -> bool:
    domain = email.rsplit("@", 1)[-1].strip().lower() if "@" in email else ""
    return domain in PLACEHOLDER_EMAIL_DOMAINS


_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)

SEVERITY_COLORS = {
    "Critical": "#dc2626",
    "Warning": "#d97706",
    "Info": "#2563eb",
}

SEVERITY_EMOJI = {
    "Critical": "\U0001F6A8",  # 🚨
    "Warning": "\u26A0\uFE0F",  # ⚠️
    "Info": "\u2139\uFE0F",  # ℹ️
}


class EmailRateLimitExceeded(Exception):
    pass


class _RateLimiter:
    """Simple in-process sliding-window rate limiter.

    Good enough for a single-process deployment. If this app is ever
    run with multiple workers, swap this for a Redis-backed limiter --
    the interface (`allow()`) would stay the same.
    """

    def __init__(self, max_per_minute: int):
        self.max_per_minute = max_per_minute
        self._timestamps: deque[float] = deque()

    def allow(self) -> bool:
        now = time.monotonic()
        while self._timestamps and now - self._timestamps[0] > 60:
            self._timestamps.popleft()

        if len(self._timestamps) >= self.max_per_minute:
            return False

        self._timestamps.append(now)
        return True


class EmailService:
    """
    Reusable SMTP email sender.

    Usage:
        email_service.send(
            to_email="ops@company.com",
            subject="Critical CPU Alert",
            title="Critical CPU Alert",
            message="CPU usage on WEB-SERVER-01 has exceeded 90%.",
            severity="Critical",
            fields=[{"label": "Asset", "value": "WEB-SERVER-01"}, ...],
        )

    Returns a dict describing the outcome -- callers persist this into
    NotificationDelivery rather than the service touching the DB
    itself (keeps this class testable/reusable outside a request).
    """

    def __init__(self):
        self._rate_limiter = _RateLimiter(settings.EMAIL_RATE_LIMIT_PER_MINUTE)

    def is_configured(self) -> bool:
        return bool(settings.SMTP_HOST and settings.SMTP_USERNAME)

    def render_html(
        self,
        title: str,
        message: str,
        severity: str = "Info",
        fields: list[dict] | None = None,
        timestamp: str | None = None,
        dashboard_url: str | None = None,
    ) -> str:
        template = _jinja_env.get_template("base.html")
        return template.render(
            title=title,
            message=message,
            severity_color=SEVERITY_COLORS.get(severity, SEVERITY_COLORS["Info"]),
            severity_emoji=SEVERITY_EMOJI.get(severity, SEVERITY_EMOJI["Info"]),
            fields=fields or [],
            timestamp=timestamp or "",
            dashboard_url=dashboard_url,
            company_name=settings.APP_NAME,
        )

    def send(
        self,
        to_email: str,
        subject: str,
        title: str,
        message: str,
        severity: str = "Info",
        fields: list[dict] | None = None,
        timestamp: str | None = None,
        dashboard_url: str | None = None,
        max_retries: int | None = None,
    ) -> dict:
        """
        Synchronous send with retry. Intended to be run inside a
        FastAPI BackgroundTask, not directly inside a request handler.
        """
        if not self.is_configured():
            return {
                "status": "Failed",
                "provider": "smtp",
                "error": "SMTP is not configured (SMTP_HOST/SMTP_USERNAME missing).",
                "latency_ms": 0,
                "retry_count": 0,
            }

        if is_placeholder_email(to_email):
            logger.warning("Refusing to send email to placeholder address: %s", to_email)
            return {
                "status": "Failed",
                "provider": "smtp",
                "error": f"Refused to send to placeholder/non-routable address: {to_email}. "
                         "This user's email should be corrected or the account deactivated.",
                "latency_ms": 0,
                "retry_count": 0,
            }

        if not self._rate_limiter.allow():
            return {
                "status": "Retrying",
                "provider": "smtp",
                "error": "Email rate limit exceeded, will retry.",
                "latency_ms": 0,
                "retry_count": 0,
            }

        html_body = self.render_html(
            title=title,
            message=message,
            severity=severity,
            fields=fields,
            timestamp=timestamp,
            dashboard_url=dashboard_url,
        )

        retries = max_retries if max_retries is not None else settings.NOTIFICATION_RETRY_COUNT
        last_error = None

        for attempt in range(1, retries + 1):
            started = time.monotonic()
            try:
                self._send_smtp(to_email, subject, html_body)
                latency_ms = int((time.monotonic() - started) * 1000)

                return {
                    "status": "Sent",
                    "provider": "smtp",
                    "response": f"Delivered on attempt {attempt}",
                    "error": None,
                    "latency_ms": latency_ms,
                    "retry_count": attempt - 1,
                }
            except Exception as exc:  # noqa: BLE001 -- log & retry any SMTP failure
                last_error = str(exc)
                logger.warning(
                    "Email send attempt %s/%s to %s failed: %s",
                    attempt, retries, to_email, last_error,
                )
                time.sleep(min(2 ** attempt, 8))  # small backoff

        return {
            "status": "Failed",
            "provider": "smtp",
            "error": last_error,
            "latency_ms": None,
            "retry_count": retries,
        }

    def _send_smtp(self, to_email: str, subject: str, html_body: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            timeout=settings.NOTIFICATION_TIMEOUT_SECONDS,
        ) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())


email_service = EmailService()
