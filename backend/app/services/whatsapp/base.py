from abc import ABC, abstractmethod


class WhatsAppProvider(ABC):
    """
    Common interface every WhatsApp provider integration implements.
    Swapping providers is a config change (WHATSAPP_PROVIDER=...), not
    a code change anywhere that calls `send()`.
    """

    name: str = "base"

    @abstractmethod
    def send(self, to_number: str, message: str) -> dict:
        """
        Send a plain-text WhatsApp message.

        Returns a dict with at least:
            {"status": "Sent" | "Failed", "response": str | None, "error": str | None}
        Never raises -- transport errors are caught and returned as a
        Failed result so the caller can log/retry uniformly.
        """
        raise NotImplementedError

    def is_configured(self) -> bool:
        return True
