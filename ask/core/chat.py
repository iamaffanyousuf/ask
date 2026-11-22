from typing import Optional

from ask.providers.openai import OpenAIProvider
from ask.providers.gemini import GeminiProvider
from ask.providers.groq import GroqProvider


def get_provider(name: str, config: dict):
    """Create the requested provider using its configured API key."""
    key = (name or "").strip().lower()

    if key == "openai":
        return OpenAIProvider(config.get("openai_api_key", ""))

    if key in {"gemini", "google"}:
        return GeminiProvider(config.get("gemini_api_key", ""))

    if key == "groq":
        return GroqProvider(config.get("groq_api_key", ""))

    raise ValueError(f"Unknown provider '{name}'. Choose openai, gemini, or groq.")


def ask_stream(
    prompt: str,
    provider_name: str,
    model: str,
    config: dict,
    history: Optional[list[dict]] = None,
):
    """Yield streamed response chunks from the selected provider."""
    provider = get_provider(provider_name, config)
    yield from provider.stream(prompt, model, history or [])


def ask_once(
    prompt: str,
    provider_name: str,
    model: str,
    config: dict,
) -> str:
    """Return a complete response from the selected provider."""
    provider = get_provider(provider_name, config)
    return provider.generate(prompt, model)
