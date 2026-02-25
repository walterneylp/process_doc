import logging

logger = logging.getLogger(__name__)


class TelegramNotifyAdapter:
    def send(self, users: list[str], message: str) -> None:
        if not users:
            return
        logger.info("notify_telegram users=%s message=%s", users, message)
