import json
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.repositories.processing_log_repository import ProcessingLogRepository
from app.schemas.ai import AskDocumentResult, ClassificationResult
from app.services.file_ingestion_service import FileIngestionService
from app.services.openrouter_client import OpenRouterClient


class AiService:
    _allowed_labels = {
        "invoice",
        "receipt",
        "contract",
        "agreement",
        "purchase_order",
        "email",
        "report",
        "dataset",
        "certificate",
        "other",
    }

    def __init__(
        self,
        document_repository: DocumentRepository | None = None,
        log_repository: ProcessingLogRepository | None = None,
        openrouter_client: OpenRouterClient | None = None,
        file_ingestion_service: FileIngestionService | None = None,
    ) -> None:
        self.document_repository = document_repository or DocumentRepository()
        self.log_repository = log_repository or ProcessingLogRepository()
        self.openrouter_client = openrouter_client or OpenRouterClient()
        self.file_ingestion_service = file_ingestion_service or FileIngestionService()

    def classify_document(self, db: Session, document_id: int, user_id: int) -> ClassificationResult:
        document = self._get_document_or_raise(db, document_id, user_id)
        self._ensure_extracted_text(db, document)
        text = self._document_text(document)

        self.log_repository.create(
            db,
            document_id=document.id,
            pipeline_step="ai_classification",
            status="started",
            message="Starting OpenRouter document classification",
        )

        rule_based = self._rule_based_classification(
            text=text,
            filename=document.filename,
            content_type=document.content_type,
        )

        if rule_based is not None:
            parsed = rule_based
            used_fallback = False
        else:
            system_prompt = (
                "You are a document classifier. Return strictly valid JSON with keys "
                "document_type, confidence, reasoning. confidence must be between 0 and 1. "
                "Allowed labels are exactly: "
                "invoice, receipt, contract, agreement, purchase_order, email, report, dataset, certificate, other."
            )
            user_prompt = (
                "Classify this document text into one of: "
                "invoice, receipt, contract, agreement, purchase_order, email, report, dataset, certificate, other.\n\n"
                f"FILENAME: {document.filename}\n"
                f"CONTENT_TYPE: {document.content_type}\n"
                f"TEXT:\n{text[:4000]}"
            )

            used_fallback = False
            try:
                raw = self.openrouter_client.chat(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.0)
            except RuntimeError as exc:
                used_fallback = True
                raw = self.openrouter_client.fallback_chat(user_prompt=user_prompt)
                self.log_repository.create(
                    db,
                    document_id=document.id,
                    pipeline_step="ai_classification",
                    status="degraded",
                    message=f"OpenRouter unavailable, used local fallback: {exc}",
                )

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
            message=(
                f"Type={parsed['document_type']}, confidence={parsed['confidence']}"
                + (" (local fallback used)" if used_fallback else "")
            ),
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

    def ask_document(self, db: Session, document_id: int, question: str, user_id: int) -> AskDocumentResult:
        document = self._get_document_or_raise(db, document_id, user_id)
        self._ensure_extracted_text(db, document)
        text = self._document_text(document)

        if not text:
            answer = (
                "I cannot answer from this file because no machine-readable text was extracted. "
                "The PDF is likely scanned/image-only. Re-upload a text-based PDF or OCR-exported file."
            )
            return AskDocumentResult(
                document_id=document.id,
                question=question,
                answer=answer,
                confidence=None,
                context_chunks_used=0,
                used_context_chars=0,
            )

        context, context_chunks_used = self._select_context(text=text, question=question)

        self.log_repository.create(
            db,
            document_id=document.id,
            pipeline_step="ai_rag",
            status="started",
            message="Starting OpenRouter RAG answer generation",
        )

        system_prompt = (
            "You are a professional AI assistant for document understanding. "
            "Answer using only the provided context and never fabricate facts."
        )
        user_prompt = (
            "Your task is to answer the user's question using ONLY the provided context.\n"
            "Instructions:\n"
            "- Do NOT return raw chunks or quote large passages verbatim\n"
            "- Summarize and explain clearly\n"
            "- Be concise but informative\n"
            "- If the question is vague, interpret it with the context and provide the most helpful explanation\n"
            "- If context is incomplete, state what is missing\n"
            "- If the answer is not present in context, say exactly: I don't know\n\n"
            f"QUESTION:\n{question}\n\n"
            f"CONTEXT:\n{context}\n\n"
            "FINAL ANSWER:"
        )

        used_fallback = False
        try:
            raw = self.openrouter_client.chat(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.2)
        except RuntimeError as exc:
            used_fallback = True
            raw = self.openrouter_client.fallback_chat(user_prompt=user_prompt)
            self.log_repository.create(
                db,
                document_id=document.id,
                pipeline_step="ai_rag",
                status="degraded",
                message=f"OpenRouter unavailable, used local fallback: {exc}",
            )

        answer = self._format_answer(raw.content)

        self.log_repository.create(
            db,
            document_id=document.id,
            pipeline_step="ai_rag",
            status="completed",
            message=(
                f"Generated answer with {len(context)} context characters"
                + (" (local fallback used)" if used_fallback else "")
            ),
        )

        db.commit()

        return AskDocumentResult(
            document_id=document.id,
            question=question,
            answer=answer,
            confidence=None,
            context_chunks_used=context_chunks_used,
            used_context_chars=len(context),
        )

    def _format_answer(self, raw_content: str) -> str:
        answer = raw_content.strip()
        answer = re.sub(r"^\s*final answer\s*:\s*", "", answer, flags=re.IGNORECASE)
        answer = re.sub(
            r"^\s*based on the document context,?\s*(the most relevant passage is:?\s*)?",
            "",
            answer,
            flags=re.IGNORECASE,
        )
        answer = re.sub(r"\s+", " ", answer).strip()
        if not answer:
            return "I don't know"
        return answer

    def _get_document_or_raise(self, db: Session, document_id: int, user_id: int) -> Document:
        document = self.document_repository.get_by_id_for_user(db, document_id, user_id)
        if document is None:
            raise ValueError(f"Document {document_id} not found")
        return document

    def _document_text(self, document: Document) -> str:
        return (document.extracted_text or "").strip()

    def _ensure_extracted_text(self, db: Session, document: Document) -> None:
        current_text = self._document_text(document)
        if current_text:
            normalized_current = self.file_ingestion_service.normalize_text(current_text)
            if normalized_current != current_text:
                document.extracted_text = normalized_current
                db.add(document)
                db.commit()
                db.refresh(document)
                self.log_repository.create(
                    db,
                    document_id=document.id,
                    pipeline_step="ai_rag",
                    status="completed",
                    message="Normalized extracted text formatting for better retrieval",
                )
            return

        try:
            extracted_text = self.file_ingestion_service.extract_from_path(
                storage_path=document.storage_path,
                original_filename=document.filename,
            )
        except ValueError as exc:
            self.log_repository.create(
                db,
                document_id=document.id,
                pipeline_step="ai_rag",
                status="warning",
                message=f"Auto-extraction skipped: {exc}",
            )
            return

        document.extracted_text = self.file_ingestion_service.normalize_text(extracted_text)
        db.add(document)
        db.commit()
        db.refresh(document)

        self.log_repository.create(
            db,
            document_id=document.id,
            pipeline_step="ai_rag",
            status="completed",
            message=f"Auto-extracted {len(document.extracted_text or '')} chars from stored file",
        )

    def _parse_classification(self, content: str) -> dict:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = re.sub(r"^json", "", cleaned, flags=re.IGNORECASE).strip()

        data = json.loads(cleaned)
        doc_type = str(data.get("document_type", "other")).lower().strip()
        if doc_type == "unknown":
            doc_type = "other"
        if doc_type not in self._allowed_labels:
            doc_type = "other"

        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
        reasoning = str(data.get("reasoning", "No reasoning provided"))

        return {
            "document_type": doc_type,
            "confidence": confidence,
            "reasoning": reasoning,
        }

    def _rule_based_classification(self, *, text: str, filename: str, content_type: str) -> dict | None:
        lowered_text = text.lower()
        lowered_filename = filename.lower()
        ext = lowered_filename.rsplit(".", 1)[-1] if "." in lowered_filename else ""

        if ext == "csv" or "text/csv" in content_type or "dataset" in lowered_filename:
            return {
                "document_type": "dataset",
                "confidence": 0.95,
                "reasoning": "Detected dataset indicators from file type and metadata.",
            }

        if any(term in lowered_text for term in ["certificate", "coursera", "issued on", "completion"]):
            return {
                "document_type": "certificate",
                "confidence": 0.9,
                "reasoning": "Detected certificate-oriented terms in document text.",
            }

        if any(term in lowered_text for term in ["purchase order", "po number", "ship to"]) and "invoice" not in lowered_text:
            return {
                "document_type": "purchase_order",
                "confidence": 0.86,
                "reasoning": "Detected purchase-order specific terms.",
            }

        if any(term in lowered_text for term in ["invoice", "amount due", "balance due", "bill to"]):
            return {
                "document_type": "invoice",
                "confidence": 0.88,
                "reasoning": "Detected invoice-specific terms.",
            }

        if any(term in lowered_text for term in ["receipt", "payment received", "transaction id", "cashier"]):
            return {
                "document_type": "receipt",
                "confidence": 0.86,
                "reasoning": "Detected receipt-specific terms.",
            }

        if any(term in lowered_text for term in ["terms and conditions", "this agreement", "effective date"]):
            return {
                "document_type": "agreement",
                "confidence": 0.82,
                "reasoning": "Detected agreement-specific legal terminology.",
            }

        if any(term in lowered_text for term in ["party", "parties", "whereas", "signature"]) and len(lowered_text) > 500:
            return {
                "document_type": "contract",
                "confidence": 0.78,
                "reasoning": "Detected contract-like legal structure and terms.",
            }

        if any(term in lowered_text for term in ["subject:", "from:", "to:", "cc:", "dear "]):
            return {
                "document_type": "email",
                "confidence": 0.8,
                "reasoning": "Detected email header and correspondence markers.",
            }

        if any(term in lowered_text for term in ["executive summary", "findings", "methodology", "conclusion"]):
            return {
                "document_type": "report",
                "confidence": 0.79,
                "reasoning": "Detected report-oriented structure and sections.",
            }

        return None

    def _select_context(self, *, text: str, question: str, chunk_size: int = 500, top_k: int = 3) -> tuple[str, int]:
        if not text:
            return "No extracted text available for this document.", 0

        words = question.lower().split()
        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

        scored: list[tuple[int, str]] = []
        for chunk in chunks:
            lowered = chunk.lower()
            score = sum(1 for w in words if w in lowered)
            scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        selected = [chunk for _, chunk in scored[:top_k]]
        return "\n\n".join(selected), len(selected)
