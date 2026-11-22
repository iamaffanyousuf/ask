from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def stream(self, prompt: str, model: str, history: list[dict]):
        """Yield text chunks for a prompt."""

    @abstractmethod
    def generate(self, prompt: str, model: str) -> str:
        """Return a complete response."""
