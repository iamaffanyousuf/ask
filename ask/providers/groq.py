from openai import OpenAI
from ask.providers.base import AIProvider


class GroqProvider(AIProvider):

    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Groq API key missing. Set GROQ_API_KEY.")

        self.client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

    def stream(self, prompt, model, history):
        messages = history + [{"role": "user", "content": prompt}]

        response = self.client.chat.completions.create(
            model=model, messages=messages, stream=True
        )

        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    def generate(self, prompt, model):
        response = self.client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content or ""
