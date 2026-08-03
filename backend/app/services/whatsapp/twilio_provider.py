import time

import httpx

from app.core.config import settings
from app.services.whatsapp.base import WhatsAppProvider

API_BASE = "https://api.twilio.com/2010-04-01"


class TwilioWhatsAppProvider(WhatsAppProvider):
    """
    Twilio WhatsApp API.
    Docs: https://www.twilio.com/docs/whatsapp/api

    Requires:
        TWILIO_ACCOUNT_SID
        WHATSAPP_TOKEN            -- used as the Twilio Auth Token
        WHATSAPP_BUSINESS_NUMBER  -- Twilio's WhatsApp-enabled "from" number
    """

    name = "twilio"

    def is_configured(self) -> bool:
        return bool(
            settings.TWILIO_ACCOUNT_SID
            and settings.WHATSAPP_TOKEN
            and settings.WHATSAPP_BUSINESS_NUMBER
        )

    def send(self, to_number: str, message: str) -> dict:
        if not self.is_configured():
            return {
                "status": "Failed",
                "response": None,
                "error": "Twilio WhatsApp is not configured (TWILIO_ACCOUNT_SID / WHATSAPP_TOKEN / WHATSAPP_BUSINESS_NUMBER missing).",
            }

        api_base = settings.WHATSAPP_API_URL or API_BASE
        url = f"{api_base}/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"

        payload = {
            "From": f"whatsapp:{settings.WHATSAPP_BUSINESS_NUMBER}",
            "To": f"whatsapp:{to_number}",
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

            return {
                "status": "Sent",
                "response": response.text,
                "error": None,
                "latency_ms": latency_ms,
            }
        except httpx.HTTPError as exc:
            return {
                "status": "Failed",
                "response": None,
                "error": str(exc),
                "latency_ms": int((time.monotonic() - started) * 1000),
            }
