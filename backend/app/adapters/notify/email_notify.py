import logging

logger = logging.getLogger(__name__)


class EmailNotifyAdapter:
    def send(self, recipients: list[str], subject: str, body: str) -> None:
        logger.info("notify_email recipients=%s subject=%s", recipients, subject)
