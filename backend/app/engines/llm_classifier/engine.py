from backend.app.adapters.llm.openai_provider import OpenAIProvider
from backend.app.engines.llm_classifier.prompts import build_classification_prompt
from backend.app.engines.llm_classifier.schemas import CLASSIFICATION_REQUIRED_KEYS


class LLMClassifierEngine:
    def __init__(self):
        self.provider = OpenAIProvider()

    def classify(self, subject: str, sender: str, body: str) -> dict:
        payload = self.provider.classify(build_classification_prompt(subject, sender, body))
        missing = CLASSIFICATION_REQUIRED_KEYS - set(payload.keys())
        if missing:
            raise ValueError(f"missing keys: {missing}")
        return payload
