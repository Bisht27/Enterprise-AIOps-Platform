from app.core.config import settings
from app.services.whatsapp.base import WhatsAppProvider
from app.services.whatsapp.meta_provider import MetaWhatsAppProvider
from app.services.whatsapp.twilio_provider import TwilioWhatsAppProvider
from app.services.whatsapp.gupshup_provider import GupshupWhatsAppProvider
from app.services.whatsapp.interakt_provider import InteraktWhatsAppProvider

_PROVIDERS: dict[str, type[WhatsAppProvider]] = {
    "meta": MetaWhatsAppProvider,
    "twilio": TwilioWhatsAppProvider,
    "gupshup": GupshupWhatsAppProvider,
    "interakt": InteraktWhatsAppProvider,
}


def get_whatsapp_provider() -> WhatsAppProvider:
    """
    Returns the provider selected by WHATSAPP_PROVIDER. Defaults to
    Meta if an unknown value is configured, rather than raising, so a
    typo in .env doesn't take down notification dispatch entirely.
    """
    provider_cls = _PROVIDERS.get(settings.WHATSAPP_PROVIDER.lower(), MetaWhatsAppProvider)
    return provider_cls()
