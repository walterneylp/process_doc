import logging

import httpx

logger = logging.getLogger(__name__)


class WebhookNotifyAdapter:
    def send(self, url: str, payload: dict) -> None:
        if not url:
            return
        try:
            with httpx.Client(timeout=8.0) as client:
                response = client.post(url, json=payload)
            logger.info("notify_webhook url=%s status=%s", url, response.status_code)
        except Exception as exc:
            logger.warning("notify_webhook_failed url=%s error=%s", url, exc)
