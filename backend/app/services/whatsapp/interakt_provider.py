import base64
import time

import httpx

from app.core.config import settings
from app.services.whatsapp.base import WhatsAppProvider

DEFAULT_API_URL = "https://api.interakt.ai/v1/public/message/"


class InteraktWhatsAppProvider(WhatsAppProvider):
    """
    Interakt WhatsApp API.
    Docs: https://developers.interakt.ai/

    Requires:
        WHATSAPP_TOKEN -- Interakt API key (sent as HTTP Basic auth,
                           per Interakt's convention of base64("<key>:"))
    """

    name = "interakt"

    def is_configured(self) -> bool:
        return bool(settings.WHATSAPP_TOKEN)

    def send(self, to_number: str, message: str) -> dict:
        if not self.is_configured():
            return {
                "status": "Failed",
                "response": None,
                "error": "Interakt WhatsApp is not configured (WHATSAPP_TOKEN missing).",
            }

        url = settings.WHATSAPP_API_URL or DEFAULT_API_URL

        auth_value = base64.b64encode(f"{settings.WHATSAPP_TOKEN}:".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_value}",
            "Content-Type": "application/json",
        }

        payload = {
            "countryCode": "",  # Interakt expects the number pre-split; caller
            "phoneNumber": to_number.lstrip("+"),
            "type": "Text",
            "data": {"message": message},
        }

        started = time.monotonic()
        try:
            response = httpx.post(
                url,
                json=payload,
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
