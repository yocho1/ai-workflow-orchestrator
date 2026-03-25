import json
from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass
class ChatResult:
    content: str


class OpenRouterClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def chat(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> ChatResult:
        if self.settings.openrouter_mock:
            return ChatResult(content=self._mock_response(user_prompt))

        if not self.settings.openrouter_api_key:
            raise RuntimeError("OpenRouter API key is not configured")

        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.settings.openrouter_referer,
            "X-Title": self.settings.openrouter_app_name,
        }

        payload = {
            "model": self.settings.openrouter_model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        with httpx.Client(timeout=self.settings.openrouter_timeout_s) as client:
            response = client.post(
                f"{self.settings.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )

        if response.status_code >= 400:
            raise RuntimeError(f"OpenRouter request failed: {response.status_code} {response.text}")

        body = response.json()
        content = body["choices"][0]["message"]["content"]
        return ChatResult(content=content)

    def _mock_response(self, user_prompt: str) -> str:
        lowered = user_prompt.lower()
        if "classify this document" in lowered or "document_type" in lowered:
            if "invoice" in lowered:
                return json.dumps(
                    {
                        "document_type": "invoice",
                        "confidence": 0.92,
                        "reasoning": "Detected invoice-related terms in document text.",
                    }
                )
            if "contract" in lowered:
                return json.dumps(
                    {
                        "document_type": "contract",
                        "confidence": 0.9,
                        "reasoning": "Detected contract-related terminology.",
                    }
                )
            if "receipt" in lowered:
                return json.dumps(
                    {
                        "document_type": "receipt",
                        "confidence": 0.88,
                        "reasoning": "Detected receipt-related terms in document text.",
                    }
                )
            return json.dumps(
                {
                    "document_type": "unknown",
                    "confidence": 0.55,
                    "reasoning": "Insufficient signal in text.",
                }
            )

        return "Based on the provided context, this document appears to contain billing details and total amount due."
