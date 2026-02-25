import json

from openai import OpenAI

from backend.app.adapters.llm.provider import LLMProvider
from backend.app.core.config import get_settings


class OpenAIProvider(LLMProvider):
    def __init__(self):
        settings = get_settings()
        self.model = settings.openai_model
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def _fallback(self, prompt: str) -> dict:
        text = (prompt or "").lower()
        if any(k in text for k in ["certificado", "treinamento", "nr-10", "nr10", "carga horária"]):
            return {
                "category": "treinamento",
                "department": "rh_seguranca",
                "confidence": 0.86,
                "priority": "normal",
                "reason": "fallback_keyword_training_certificate",
            }
        if any(k in text for k in ["nota fiscal", "nf-e", "nfe", "nfse", "danfe", "fatura", "boleto"]):
            return {
                "category": "fiscal",
                "department": "financeiro",
                "confidence": 0.82,
                "priority": "high",
                "reason": "fallback_keyword_fiscal",
            }
        if any(k in text for k in ["boleto", "pagamento", "vencimento"]):
            return {
                "category": "financeiro",
                "department": "financeiro",
                "confidence": 0.8,
                "priority": "high",
                "reason": "fallback_keyword_financeiro",
            }
        return {
            "category": "generic",
            "department": "triage",
            "confidence": 0.65,
            "priority": "normal",
            "reason": "fallback_no_api_key",
        }

    def classify(self, prompt: str) -> dict:
        if not self.client:
            return self._fallback(prompt)
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
