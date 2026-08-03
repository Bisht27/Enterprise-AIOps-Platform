import time
import httpx

from app.core.config import settings
from app.services.whatsapp.base import WhatsAppProvider

DEFAULT_API_BASE = "https://graph.facebook.com/v20.0"


class MetaWhatsAppProvider(WhatsAppProvider):
    """
    Meta (Facebook) WhatsApp Cloud API
    """

    name = "meta"

    def is_configured(self) -> bool:
        return bool(
            settings.WHATSAPP_TOKEN
            and settings.WHATSAPP_PHONE_NUMBER_ID
        )

    def send(self, to_number: str, message: str) -> dict:
        if not self.is_configured():
            return {
                "status": "Failed",
                "response": None,
                "error": "Meta WhatsApp is not configured.",
            }

        api_base = settings.WHATSAPP_API_URL or DEFAULT_API_BASE

        url = f"{api_base}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"

        payload = {
    "messaging_product": "whatsapp",
    "recipient_type": "individual",
    "to": to_number,
    "type": "text",
    "text": {
        "preview_url": False,
        "body": message,
    },
}

        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
            "Content-Type": "application/json",
        }

        print("\n================ META WHATSAPP =================")
        print("URL:", url)
        print("Recipient:", to_number)
        print("Message Length:", len(message))
        print("Message:")
        print(message)
        print("-----------------------------------------------")
        print("Payload:", payload)
        print("===============================================\n")

        started = time.monotonic()

        try:
            response = httpx.post(
                url,
                headers=headers,
                json=payload,
                timeout=settings.NOTIFICATION_TIMEOUT_SECONDS,
            )

            latency = int((time.monotonic() - started) * 1000)

            print("\n============= META RESPONSE ===================")
            print("Status Code :", response.status_code)
            print("Response    :", response.text)
            print("Latency(ms) :", latency)
            print("===============================================\n")

            if response.status_code >= 400:
                return {
                    "status": "Failed",
                    "response": response.text,
                    "error": f"HTTP {response.status_code}",
                    "latency_ms": latency,
                }

            return {
                "status": "Sent",
                "response": response.text,
                "error": None,
                "latency_ms": latency,
            }

        except Exception as exc:
            print("\n============= META EXCEPTION ==================")
            print(exc)
            print("===============================================\n")

            return {
                "status": "Failed",
                "response": None,
                "error": str(exc),
                "latency_ms": None,
            }