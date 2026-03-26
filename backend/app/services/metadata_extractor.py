"""Service for extracting and classifying document metadata using AI."""

import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.enums import DocumentType
from app.models.metadata import DocumentMetadata
from app.repositories.metadata_repository import MetadataRepository
from app.schemas.metadata import MetadataCreate, MetadataUpdate
from app.services.ai_service import AiService


class MetadataExtractor:
    """Extracts structured metadata from document text using AI."""

    # Prompts for different document types
    CLASSIFICATION_PROMPT = """Analyze the document text below and classify it into one of these categories:
    - invoice: Sales invoice, purchase invoice, bill
    - contract: Legal agreement, business contract, SLA
    - receipt: Purchase receipt, transaction record, proof of payment
    - report: Business report, financial statement, analysis
    - other: Something else or unclear

    Respond with ONLY this JSON format, no other text:
    {{"document_type": "invoice|contract|receipt|report|other", "confidence": 0.0-1.0, "reason": "brief explanation"}}

    Document text:
    {{text}}"""

    INVOICE_EXTRACTION_PROMPT = """Extract the following information from the invoice text below. Return ONLY valid JSON.
    Return null for any field you cannot find.

    {{"amount": number, "currency": "string", "invoice_number": "string", "date": "YYYY-MM-DD or null", "due_date": "YYYY-MM-DD or null", "vendor": "string", "line_items": [{{"description": "string", "quantity": number, "unit_price": number, "total": number}}]}}

    Invoice text:
    {{text}}"""

    CONTRACT_EXTRACTION_PROMPT = """Extract the following information from the contract text below. Return ONLY valid JSON.
    Return null for any field you cannot find.

    {{"parties": ["string"], "start_date": "YYYY-MM-DD or null", "end_date": "YYYY-MM-DD or null", "expiration_date": "YYYY-MM-DD or null", "key_clauses": ["string", "..."], "termination_clause": "string"}}

    Contract text:
    {{text}}"""

    RECEIPT_EXTRACTION_PROMPT = """Extract the following information from the receipt text below. Return ONLY valid JSON.
    Return null for any field you cannot find.

    {{"amount": number, "currency": "string", "date": "YYYY-MM-DD or null", "merchant": "string", "items": [{{"description": "string", "quantity": number, "price": number}}]}}

    Receipt text:
    {{text}}"""

    def __init__(self, ai_service: AiService | None = None) -> None:
        """Initialize extractor with optional AI service dependency."""
        self.ai_service = ai_service or AiService()
        self.settings = get_settings()

    def classify_document(self, text: str) -> tuple[str, float]:
        """Classify document type and return (type, confidence_score)."""
        prompt = self.CLASSIFICATION_PROMPT.replace("{{text}}", text[:2000])
        response = self.ai_service.openrouter_client.chat(
            system_prompt="You are a document classifier. Respond with valid JSON only.",
            user_prompt=prompt,
            temperature=0.1,
        )

        try:
            result = json.loads(response.content)
            doc_type = result.get("document_type", DocumentType.OTHER)
            confidence = float(result.get("confidence", 0.0))
            return doc_type, confidence
        except (json.JSONDecodeError, ValueError, KeyError):
            return DocumentType.OTHER, 0.0

    def extract_invoice_data(self, text: str) -> dict[str, Any]:
        """Extract invoice-specific fields."""
        prompt = self.INVOICE_EXTRACTION_PROMPT.replace("{{text}}", text[:3000])
        response = self.ai_service.openrouter_client.chat(
            system_prompt="You are a document data extractor. Return only valid JSON.",
            user_prompt=prompt,
            temperature=0.1,
        )

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {}

    def extract_contract_data(self, text: str) -> dict[str, Any]:
        """Extract contract-specific fields."""
        prompt = self.CONTRACT_EXTRACTION_PROMPT.replace("{{text}}", text[:3000])
        response = self.ai_service.openrouter_client.chat(
            system_prompt="You are a document data extractor. Return only valid JSON.",
            user_prompt=prompt,
            temperature=0.1,
        )

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {}

    def extract_receipt_data(self, text: str) -> dict[str, Any]:
        """Extract receipt-specific fields."""
        prompt = self.RECEIPT_EXTRACTION_PROMPT.replace("{{text}}", text[:3000])
        response = self.ai_service.openrouter_client.chat(
            system_prompt="You are a document data extractor. Return only valid JSON.",
            user_prompt=prompt,
            temperature=0.1,
        )

        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {}

    def extract_metadata(
        self,
        db: Session,
        document_id: int,
        text: str,
    ) -> DocumentMetadata:
        """
        Extract metadata from document text.
        
        1. Classify document type
        2. Extract type-specific fields
        3. Store in database
        """
        try:
            # Step 1: Classify document
            doc_type, confidence = self.classify_document(text)

            # Step 2: Extract type-specific data
            extracted_data = {}
            if doc_type == DocumentType.INVOICE:
                extracted_data = self.extract_invoice_data(text)
            elif doc_type == DocumentType.CONTRACT:
                extracted_data = self.extract_contract_data(text)
            elif doc_type == DocumentType.RECEIPT:
                extracted_data = self.extract_receipt_data(text)
            # For REPORT and OTHER, just store document type

            # Step 3: Store metadata
            repo = MetadataRepository()
            threshold = self.settings.metadata_review_threshold
            needs_review = confidence < threshold
            review_reason = (
                f"Low confidence ({confidence:.2f}) below threshold ({threshold:.2f})"
                if needs_review
                else None
            )
            payload = MetadataCreate(
                document_type=doc_type,
                confidence_score=confidence,
                extracted_data=extracted_data,
                extraction_model="openai/gpt-4o-mini",
                extraction_error=None,
                needs_review=needs_review,
                review_reason=review_reason,
            )
            existing = repo.get_by_document_id(db, document_id)
            if existing:
                updated = repo.update(
                    db,
                    existing.id,
                    MetadataUpdate(
                        document_type=payload.document_type,
                        confidence_score=payload.confidence_score,
                        extracted_data=payload.extracted_data,
                        needs_review=payload.needs_review,
                        review_reason=payload.review_reason,
                    ),
                )
                if not updated:
                    raise RuntimeError("Failed to update existing metadata")
                metadata = updated
            else:
                metadata = repo.create(db, document_id, payload)
            return metadata

        except Exception as e:
            # If extraction fails, create error record
            repo = MetadataRepository()
            payload = MetadataCreate(
                document_type=DocumentType.OTHER,
                confidence_score=0.0,
                extracted_data={},
                extraction_model="openai/gpt-4o-mini",
                extraction_error=str(e),
                needs_review=True,
                review_reason="Extraction failed and requires manual review",
            )
            existing = repo.get_by_document_id(db, document_id)
            if existing:
                updated = repo.update(
                    db,
                    existing.id,
                    MetadataUpdate(
                        document_type=payload.document_type,
                        confidence_score=payload.confidence_score,
                        extracted_data=payload.extracted_data,
                        needs_review=payload.needs_review,
                        review_reason=payload.review_reason,
                    ),
                )
                if not updated:
                    raise RuntimeError("Failed to update existing metadata after extraction error")
                metadata = updated
            else:
                metadata = repo.create(db, document_id, payload)
            return metadata
