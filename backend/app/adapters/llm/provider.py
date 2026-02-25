from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def classify(self, prompt: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def extract(self, prompt: str) -> dict:
        raise NotImplementedError
