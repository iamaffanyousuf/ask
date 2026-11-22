from openai import OpenAI
from ask.providers.base import AIProvider


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OpenAI API key missing. Run `ask setup` or set OPENAI_API_KEY.")
        self.client = OpenAI(api_key=api_key)

    def stream(self, prompt: str, model: str, history: list[dict]):
        messages = list(history) + [{"role": "user", "content": prompt}]
        stream = self.client.chat.completions.create(
            model=model, messages=messages, stream=True
        )
        for event in stream:
            if event.choices and event.choices[0].delta.content:
                yield event.choices[0].delta.content

    def generate(self, prompt: str, model: str) -> str:
        result = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return result.choices[0].message.content or ""
