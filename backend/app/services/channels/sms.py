import time

import httpx

from app.core.config import settings

API_BASE = "https://api.twilio.com/2010-04-01"


def is_sms_configured() -> bool:
    return bool(
        settings.TWILIO_ACCOUNT_SID
        and settings.WHATSAPP_TOKEN  # reused as the Twilio Auth Token
        and settings.TWILIO_SMS_FROM_NUMBER
    )


def send_sms(to_number: str, message: str) -> dict:
    """
    Sends a plain SMS via Twilio.
    Docs: https://www.twilio.com/docs/sms/api

    Requires:
        TWILIO_ACCOUNT_SID
        WHATSAPP_TOKEN          -- reused as the Twilio Auth Token
        TWILIO_SMS_FROM_NUMBER  -- a Twilio phone number (not the
                                    WhatsApp-enabled one)
    """
    if not is_sms_configured():
        return {
            "status": "Failed",
            "response": None,
            "error": "SMS is not configured (TWILIO_ACCOUNT_SID / WHATSAPP_TOKEN / TWILIO_SMS_FROM_NUMBER missing).",
        }

    url = f"{API_BASE}/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
    payload = {
        "From": settings.TWILIO_SMS_FROM_NUMBER,
        "To": to_number,
        "Body": message,
    }

    started = time.monotonic()
    try:
        response = httpx.post(
            url,
            data=payload,
            auth=(settings.TWILIO_ACCOUNT_SID, settings.WHATSAPP_TOKEN),
            timeout=settings.NOTIFICATION_TIMEOUT_SECONDS,
        )
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
