import logging

logger = logging.getLogger(__name__)


class WebhookNotifyAdapter:
    def send(self, url: str, payload: dict) -> None:
        logger.info("notify_webhook url=%s payload=%s", url, payload)
