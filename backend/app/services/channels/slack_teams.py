import time

import httpx

from app.core.config import settings


def send_slack_message(webhook_url: str, title: str, message: str) -> dict:
    """
    Posts to a Slack "Incoming Webhook" URL.
    Docs: https://api.slack.com/messaging/webhooks

    The webhook URL is per-user (set on their NotificationPreference),
    not a platform-wide credential, since Slack webhooks are tied to a
    specific channel a specific person set up.
    """
    if not webhook_url:
        return {"status": "Failed", "response": None, "error": "No Slack webhook URL configured."}

    payload = {
        "text": f"*{title}*\n{message}",
    }

    started = time.monotonic()
    try:
        response = httpx.post(webhook_url, json=payload, timeout=settings.NOTIFICATION_TIMEOUT_SECONDS)
        latency_ms = int((time.monotonic() - started) * 1000)

        if response.status_code >= 400:
            return {
                "status": "Failed",
                "response": response.text,
                "error": f"HTTP {response.status_code}",
                "latency_ms": latency_ms,
            }

        return {"status": "Sent", "response": response.text, "error": None, "latency_ms": latency_ms}
    except httpx.HTTPError as exc:
        return {
            "status": "Failed",
            "response": None,
            "error": str(exc),
            "latency_ms": int((time.monotonic() - started) * 1000),
        }


def send_teams_message(webhook_url: str, title: str, message: str, severity: str = "Info") -> dict:
    """
    Posts to a Microsoft Teams "Incoming Webhook" connector using the
    legacy MessageCard format (still the widest-compatible option
    across Teams webhook connectors).
    Docs: https://learn.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/connectors-using
    """
    if not webhook_url:
        return {"status": "Failed", "response": None, "error": "No Teams webhook URL configured."}

    color = {"Critical": "dc2626", "Warning": "d97706", "Info": "2563eb"}.get(severity, "2563eb")

    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": color,
        "summary": title,
        "title": title,
        "text": message,
    }

    started = time.monotonic()
    try:
        response = httpx.post(webhook_url, json=payload, timeout=settings.NOTIFICATION_TIMEOUT_SECONDS)
        latency_ms = int((time.monotonic() - started) * 1000)

        if response.status_code >= 400:
            return {
                "status": "Failed",
                "response": response.text,
                "error": f"HTTP {response.status_code}",
                "latency_ms": latency_ms,
            }

        return {"status": "Sent", "response": response.text, "error": None, "latency_ms": latency_ms}
    except httpx.HTTPError as exc:
        return {
            "status": "Failed",
            "response": None,
            "error": str(exc),
            "latency_ms": int((time.monotonic() - started) * 1000),
        }
