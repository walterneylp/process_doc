import logging

logger = logging.getLogger(__name__)


class WhatsAppNotifyAdapter:
    def send(self, numbers: list[str], message: str) -> None:
        if not numbers:
            return
        logger.info("notify_whatsapp numbers=%s message=%s", numbers, message)
