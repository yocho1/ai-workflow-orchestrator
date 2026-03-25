import json
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.repositories.processing_log_repository import ProcessingLogRepository
from app.schemas.ai import AskDocumentResult, ClassificationResult
from app.services.openrouter_client import OpenRouterClient


class AiService:
    def __init__(
        self,
        document_repository: DocumentRepository | None = None,
        log_repository: ProcessingLogRepository | None = None,
        openrouter_client: OpenRouterClient | None = None,
    ) -> None:
        self.document_repository = document_repository or DocumentRepository()
        self.log_repository = log_repository or ProcessingLogRepository()
        self.openrouter_client = openrouter_client or OpenRouterClient()

    def classify_document(self, db: Session, document_id: int) -> ClassificationResult:
        document = self._get_document_or_raise(db, document_id)
        text = self._document_text(document)

        self.log_repository.create(
            db,
            document_id=document.id,
            pipeline_step="ai_classification",
            status="started",
            message="Starting OpenRouter document classification",
        )

        system_prompt = (
            "You are a document classifier. Return strictly valid JSON with keys "
            "document_type, confidence, reasoning. confidence must be between 0 and 1."
        )
        user_prompt = (
            "Classify this document text into one of: invoice, contract, receipt, unknown.\n\n"
            f"TEXT:\n{text[:4000]}"
        )

        raw = self.openrouter_client.chat(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.0)
        try:
            parsed = self._parse_classification(raw.content)
        except Exception as exc:
            raise RuntimeError("Failed to parse OpenRouter classification response") from exc

        document.document_type = parsed["document_type"]
        document.processing_status = "classified"
        db.add(document)

        self.log_repository.create(
            db,
            document_id=document.id,
            pipeline_step="ai_classification",
            status="completed",
            message=f"Type={parsed['document_type']}, confidence={parsed['confidence']}",
        )

        db.commit()
        db.refresh(document)

        return ClassificationResult(
            document_id=document.id,
            document_type=document.document_type,
            confidence=parsed["confidence"],
            reasoning=parsed["reasoning"],
            updated_at=document.updated_at,
        )

    def ask_document(self, db: Session, document_id: int, question: str) -> AskDocumentResult:
        document = self._get_document_or_raise(db, document_id)
        text = self._document_text(document)
        context = self._select_context(text=text, question=question)

        self.log_repository.create(
            db,
            document_id=document.id,
            pipeline_step="ai_rag",
            status="started",
            message="Starting OpenRouter RAG answer generation",
        )

        system_prompt = (
            "You are a retrieval QA assistant. Use only the given context. "
            "If context is insufficient, clearly say so."
        )
        user_prompt = (
            f"QUESTION:\n{question}\n\n"
            f"CONTEXT:\n{context}"
        )

        raw = self.openrouter_client.chat(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.2)
        answer = raw.content.strip()

        self.log_repository.create(
            db,
            document_id=document.id,
            pipeline_step="ai_rag",
            status="completed",
            message=f"Generated answer with {len(context)} context characters",
        )

        db.commit()

        return AskDocumentResult(
            document_id=document.id,
            question=question,
            answer=answer,
            used_context_chars=len(context),
        )

    def _get_document_or_raise(self, db: Session, document_id: int) -> Document:
        document = self.document_repository.get_by_id(db, document_id)
        if document is None:
            raise ValueError(f"Document {document_id} not found")
        return document

    def _document_text(self, document: Document) -> str:
        return (document.extracted_text or "").strip()

    def _parse_classification(self, content: str) -> dict:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = re.sub(r"^json", "", cleaned, flags=re.IGNORECASE).strip()

        data = json.loads(cleaned)
        doc_type = str(data.get("document_type", "unknown")).lower()
        if doc_type not in {"invoice", "contract", "receipt", "unknown"}:
            doc_type = "unknown"

        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
        reasoning = str(data.get("reasoning", "No reasoning provided"))

        return {
            "document_type": doc_type,
            "confidence": confidence,
            "reasoning": reasoning,
        }

    def _select_context(self, *, text: str, question: str, chunk_size: int = 500, top_k: int = 3) -> str:
        if not text:
            return "No extracted text available for this document."

        words = question.lower().split()
        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

        scored: list[tuple[int, str]] = []
        for chunk in chunks:
            lowered = chunk.lower()
            score = sum(1 for w in words if w in lowered)
            scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        selected = [chunk for _, chunk in scored[:top_k]]
        return "\n\n".join(selected)
