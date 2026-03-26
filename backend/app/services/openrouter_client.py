import json
import re
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

    def fallback_chat(self, *, user_prompt: str) -> ChatResult:
        return ChatResult(content=self._mock_response(user_prompt))

    def _mock_response(self, user_prompt: str) -> str:
        lowered = user_prompt.lower()
        if "classify this document" in lowered or "document_type" in lowered:
            return self._mock_classification_response(user_prompt)

        question, context = self._extract_question_and_context(user_prompt)
        return self._mock_answer_from_context(question=question, context=context)

    def _extract_question_and_context(self, user_prompt: str) -> tuple[str, str]:
        question_match = re.search(r"QUESTION:\s*(.*?)\s*(?:CONTEXT:|$)", user_prompt, flags=re.DOTALL | re.IGNORECASE)
        context_match = re.search(r"CONTEXT:\s*(.*)$", user_prompt, flags=re.DOTALL | re.IGNORECASE)

        question = question_match.group(1).strip() if question_match else ""
        context = context_match.group(1).strip() if context_match else user_prompt.strip()
        return question, context

    def _mock_answer_from_context(self, *, question: str, context: str) -> str:
        if not context:
            return "I cannot answer because the document has no extracted text."

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", context) if s.strip()]
        if not sentences:
            return "I found document text, but not enough structured content to answer confidently."

        query_terms = [w for w in re.findall(r"[a-zA-Z0-9]+", question.lower()) if len(w) > 2]

        if "name" in question.lower():
            name = self._extract_probable_name(context)
            if name:
                return f"The name in the document appears to be: {name}."

        best_sentence = sentences[0]
        best_score = -1
        for sentence in sentences[:40]:
            lowered_sentence = sentence.lower()
            score = sum(1 for term in query_terms if term in lowered_sentence)
            if score > best_score:
                best_score = score
                best_sentence = sentence

        if best_score <= 0 and len(sentences) > 1:
            preview = " ".join(sentences[:2])
            return (
                "I could not find a direct match to your question in the selected context. "
                f"Document summary: {preview[:320]}"
            )

        lead = "The document indicates"
        if "tax" in question.lower():
            lead = "The document explains tax-related obligations"
        return f"{lead} that {best_sentence[:320]}"

    def _mock_classification_response(self, user_prompt: str) -> str:
        text = self._extract_classification_text(user_prompt).lower()

        if any(term in text for term in ["certificate", "coursera", "course", "completion", "issued on"]):
            return json.dumps(
                {
                    "document_type": "certificate",
                    "confidence": 0.88,
                    "reasoning": "Document appears to be a certificate/learning record.",
                }
            )

        if any(term in text for term in ["purchase order", "po number", "ship to"]) and "invoice" not in text:
            return json.dumps(
                {
                    "document_type": "purchase_order",
                    "confidence": 0.84,
                    "reasoning": "Detected purchase-order specific terms.",
                }
            )

        if any(term in text for term in ["subject:", "from:", "to:", "cc:"]):
            return json.dumps(
                {
                    "document_type": "email",
                    "confidence": 0.8,
                    "reasoning": "Detected email header structure.",
                }
            )

        if any(term in text for term in ["executive summary", "findings", "methodology", "conclusion"]):
            return json.dumps(
                {
                    "document_type": "report",
                    "confidence": 0.79,
                    "reasoning": "Detected report structure and section terms.",
                }
            )

        if any(term in text for term in [",", "\n"]) and any(term in text for term in ["dataset", "rows", "columns"]):
            return json.dumps(
                {
                    "document_type": "dataset",
                    "confidence": 0.78,
                    "reasoning": "Detected data-table or dataset-oriented content.",
                }
            )

        scores = {
            "invoice": sum(1 for term in ["invoice", "amount due", "subtotal", "tax", "balance due", "bill to", "payment due"] if term in text),
            "receipt": sum(1 for term in ["receipt", "paid", "payment received", "cashier", "transaction id", "thank you"] if term in text),
            "agreement": sum(1 for term in ["agreement", "terms and conditions", "effective date"] if term in text),
            "contract": sum(1 for term in ["party", "parties", "whereas", "signature"] if term in text),
        }

        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        if best_score == 0:
            return json.dumps(
                {
                    "document_type": "other",
                    "confidence": 0.55,
                    "reasoning": "Insufficient signal in text.",
                }
            )

        confidence = min(0.95, 0.6 + (0.1 * best_score))
        return json.dumps(
            {
                "document_type": best_type,
                "confidence": confidence,
                "reasoning": f"Detected {best_type}-related terms in document text.",
            }
        )

    def _extract_classification_text(self, user_prompt: str) -> str:
        marker = "TEXT:"
        idx = user_prompt.find(marker)
        if idx == -1:
            return user_prompt
        return user_prompt[idx + len(marker) :].strip()

    def _extract_probable_name(self, text: str) -> str | None:
        months = {
            "jan", "january", "feb", "february", "mar", "march", "apr", "april", "may", "jun", "june",
            "jul", "july", "aug", "august", "sep", "sept", "september", "oct", "october", "nov",
            "november", "dec", "december",
        }

        for line in text.splitlines():
            candidates = re.findall(r"\b([A-Z][a-z]+(?: +[A-Z][a-z]+){1,3})\b", line)
            for candidate in candidates:
                parts = candidate.split()
                first = parts[0].lower()
                if first in months:
                    continue
                if any(any(ch.isdigit() for ch in part) for part in parts):
                    continue
                return candidate
        return None
