from google import genai
from ask.providers.base import AIProvider


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API key missing. Run `ask setup` or set GEMINI_API_KEY.")
        self.client = genai.Client(api_key=api_key)

    def stream(self, prompt: str, model: str, history: list[dict]):
        # Gemini chat history uses user/model roles.
        chat = self.client.chats.create(
            model=model,
            history=[
                {"role": "user" if item["role"] == "user" else "model",
                 "parts": [{"text": item["content"]}]}
                for item in history
            ],
        )
        for chunk in chat.send_message_stream(prompt):
            if getattr(chunk, "text", None):
                yield chunk.text

    def generate(self, prompt: str, model: str) -> str:
        response = self.client.models.generate_content(model=model, contents=prompt)
        return response.text or ""
