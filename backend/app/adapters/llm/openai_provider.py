import json

from openai import OpenAI

from backend.app.adapters.llm.provider import LLMProvider
from backend.app.core.config import get_settings


class OpenAIProvider(LLMProvider):
    def __init__(self):
        settings = get_settings()
        self.model = settings.openai_model
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def _fallback(self) -> dict:
        return {
            "category": "generic",
            "department": "triage",
            "confidence": 0.6,
            "priority": "normal",
            "reason": "fallback_no_api_key",
        }

    def classify(self, prompt: str) -> dict:
        if not self.client:
            return self._fallback()
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            text={"format": {"type": "json_object"}},
        )
        return json.loads(response.output_text)

    def extract(self, prompt: str) -> dict:
        if not self.client:
            return {"fields": {}}
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            text={"format": {"type": "json_object"}},
        )
        return json.loads(response.output_text)
