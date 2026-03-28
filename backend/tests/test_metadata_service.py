"""Unit tests for metadata extraction service."""

import json
import pytest
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session

from app.models.enums import DocumentType
from app.models.metadata import DocumentMetadata
from app.repositories.metadata_repository import MetadataRepository
from app.schemas.metadata import MetadataCreate
from app.services.metadata_extractor import MetadataExtractor
from app.services.metadata_service import MetadataService


class TestMetadataRepository:
    """Tests for MetadataRepository."""

    def test_create_metadata(self, db: Session):
        """Test creating a new metadata record."""
        repo = MetadataRepository()
        payload = MetadataCreate(
            document_type=DocumentType.INVOICE,
            confidence_score=0.95,
            extracted_data={"amount": 100.00, "currency": "USD"},
        )

        metadata = repo.create(db, document_id=1, payload=payload)
        db.commit()

        assert metadata.document_id == 1
        assert metadata.document_type == DocumentType.INVOICE
        assert metadata.confidence_score == 0.95
        assert metadata.extracted_data == {"amount": 100.00, "currency": "USD"}

    def test_get_by_document_id(self, db: Session):
        """Test retrieving metadata by document ID."""
        repo = MetadataRepository()
        payload = MetadataCreate(
            document_type=DocumentType.CONTRACT,
            confidence_score=0.88,
            extracted_data={"parties": ["Company A", "Company B"]},
        )
        created = repo.create(db, 2, payload)
        db.commit()

        retrieved = repo.get_by_document_id(db, 2)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.document_type == DocumentType.CONTRACT

    def test_get_nonexistent_metadata(self, db: Session):
        """Test retrieving nonexistent metadata."""
        repo = MetadataRepository()
        retrieved = repo.get_by_document_id(db, 99999)
        assert retrieved is None

    def test_update_metadata(self, db: Session):
        """Test updating metadata."""
        repo = MetadataRepository()
        payload = MetadataCreate(
            document_type=DocumentType.RECEIPT,
            confidence_score=0.75,
            extracted_data={"merchant": "Store A"},
        )
        metadata = repo.create(db, 3, payload)
        db.commit()

        from app.schemas.metadata import MetadataUpdate

        update_payload = MetadataUpdate(
            confidence_score=0.85,
            extracted_data={"merchant": "Store B", "amount": 25.50},
        )
        updated = repo.update(db, metadata.id, update_payload)
        db.commit()

        assert updated is not None
        assert updated.confidence_score == 0.85
        assert updated.extracted_data["merchant"] == "Store B"


class TestMetadataExtractor:
    """Tests for MetadataExtractor service."""

    @patch("app.services.metadata_extractor.AiService")
    def test_classify_document_invoice(self, mock_ai_service):
        """Test invoice classification."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = json.dumps(
            {"document_type": "invoice", "confidence": 0.95, "reason": "Contains amount and date"}
        )
        mock_client.chat.return_value = mock_response

        mock_ai_instance = Mock()
        mock_ai_instance.openrouter_client = mock_client
        mock_ai_service.return_value = mock_ai_instance

        extractor = MetadataExtractor(ai_service=mock_ai_instance)
        doc_type, confidence = extractor.classify_document("Invoice #12345 Amount: $100")

        assert doc_type == "invoice"
        assert confidence == 0.95
        mock_client.chat.assert_called_once()

    @patch("app.services.metadata_extractor.AiService")
    def test_classify_document_invalid_response(self, mock_ai_service):
        """Test classification with invalid AI response."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = "Not valid JSON"
        mock_client.chat.return_value = mock_response

        mock_ai_instance = Mock()
        mock_ai_instance.openrouter_client = mock_client
        mock_ai_service.return_value = mock_ai_instance

        extractor = MetadataExtractor(ai_service=mock_ai_instance)
        doc_type, confidence = extractor.classify_document("Some document")

        assert doc_type == DocumentType.OTHER
        assert confidence == 0.0

    @patch("app.services.metadata_extractor.AiService")
    def test_extract_invoice_data(self, mock_ai_service):
        """Test invoice data extraction."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = json.dumps(
            {
                "amount": 150.00,
                "currency": "USD",
                "invoice_number": "INV-001",
                "date": "2026-03-26",
            }
        )
        mock_client.chat.return_value = mock_response

        mock_ai_instance = Mock()
        mock_ai_instance.openrouter_client = mock_client
        mock_ai_service.return_value = mock_ai_instance

        extractor = MetadataExtractor(ai_service=mock_ai_instance)
        data = extractor.extract_invoice_data("Invoice content...")

        assert data["amount"] == 150.00
        assert data["currency"] == "USD"
        assert data["invoice_number"] == "INV-001"

    @patch("app.services.metadata_extractor.AiService")
    def test_extract_metadata_full_pipeline(self, mock_ai_service, db: Session):
        """Test full metadata extraction pipeline."""
        # Mock classification
        classification_response = Mock()
        classification_response.content = json.dumps(
            {"document_type": "invoice", "confidence": 0.92, "reason": ""}
        )

        # Mock extraction
        extraction_response = Mock()
        extraction_response.content = json.dumps(
            {
                "amount": 200.00,
                "currency": "USD",
                "invoice_number": "INV-002",
                "date": "2026-03-26",
            }
        )

        mock_client = Mock()
        mock_client.chat.side_effect = [classification_response, extraction_response]

        mock_ai_instance = Mock()
        mock_ai_instance.openrouter_client = mock_client
        mock_ai_service.return_value = mock_ai_instance

        extractor = MetadataExtractor(ai_service=mock_ai_instance)
        metadata = extractor.extract_metadata(db, document_id=1, text="Invoice #INV-002...")
        db.commit()

        assert metadata.document_type == "invoice"
        assert metadata.confidence_score == 0.92
        assert metadata.extracted_data["amount"] == 200.00
        assert metadata.extraction_error is None


class TestMetadataService:
    """Tests for MetadataService."""

    @patch("app.services.metadata_service.MetadataExtractor")
    @patch("app.services.metadata_service.DocumentStatusService")
    def test_process_and_extract_success(
        self, mock_status_service, mock_extractor, db: Session, test_document
    ):
        """Test successful metadata processing and status transitions."""
        # Mock metadata extraction
        mock_metadata = Mock(spec=DocumentMetadata)
        mock_metadata.document_type = DocumentType.INVOICE
        mock_metadata.confidence_score = 0.9
        mock_metadata.extraction_error = None

        mock_extractor_instance = Mock()
        mock_extractor_instance.extract_metadata.return_value = mock_metadata
        mock_extractor.return_value = mock_extractor_instance

        # Mock status service
        mock_status_instance = Mock()
        mock_status_service.return_value = mock_status_instance

        service = MetadataService(
            extractor=mock_extractor_instance,
            status_service=mock_status_instance,
        )

        service.process_and_extract(db, test_document, "Invoice text...")

        # Verify extraction was called
        mock_extractor_instance.extract_metadata.assert_called_once()

        # Verify status transitions
        assert mock_status_instance.update_status.call_count == 3

    @patch("app.services.metadata_service.MetadataExtractor")
    @patch("app.services.metadata_service.DocumentStatusService")
    def test_process_and_extract_no_text(
        self, mock_status_service, mock_extractor, db: Session, test_document
    ):
        """Test processing document with no extracted text."""
        test_document.extracted_text = None

        mock_extractor_instance = Mock()
        mock_status_instance = Mock()
        mock_status_service.return_value = mock_status_instance

        service = MetadataService(
            extractor=mock_extractor_instance,
            status_service=mock_status_instance,
        )

        service.process_and_extract(db, test_document)

        # Should transition to FAILED
        mock_status_instance.update_status.assert_called_once()
        call_args = mock_status_instance.update_status.call_args
        assert "No text available" in call_args[0][3]  # Check message parameter
