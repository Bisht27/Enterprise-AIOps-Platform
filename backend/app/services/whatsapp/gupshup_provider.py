import time

import httpx

from app.core.config import settings
from app.services.whatsapp.base import WhatsAppProvider

DEFAULT_API_URL = "https://api.gupshup.io/wa/api/v1/msg"


class GupshupWhatsAppProvider(WhatsAppProvider):
    """
    Gupshup WhatsApp API.
    Docs: https://docs.gupshup.io/reference/whatsapp-messaging-api

    Requires:
        WHATSAPP_TOKEN            -- Gupshup API key
        GUPSHUP_APP_NAME          -- your registered Gupshup app name
        WHATSAPP_BUSINESS_NUMBER  -- your Gupshup source number
    """

    name = "gupshup"

    def is_configured(self) -> bool:
        return bool(
            settings.WHATSAPP_TOKEN
            and settings.GUPSHUP_APP_NAME
            and settings.WHATSAPP_BUSINESS_NUMBER
        )

    def send(self, to_number: str, message: str) -> dict:
        if not self.is_configured():
            return {
                "status": "Failed",
                "response": None,
                "error": "Gupshup WhatsApp is not configured (WHATSAPP_TOKEN / GUPSHUP_APP_NAME / WHATSAPP_BUSINESS_NUMBER missing).",
            }

        url = settings.WHATSAPP_API_URL or DEFAULT_API_URL

        payload = {
            "channel": "whatsapp",
            "source": settings.WHATSAPP_BUSINESS_NUMBER,
            "destination": to_number,
            "src.name": settings.GUPSHUP_APP_NAME,
            "message": f'{{"type":"text","text":"{message}"}}',
        }
        headers = {
            "apikey": settings.WHATSAPP_TOKEN,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        started = time.monotonic()
        try:
            response = httpx.post(
                url,
                data=payload,
                headers=headers,
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
