"""Integration tests for metadata API endpoints."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.models.enums import DocumentStatus


def _metadata_ns(document_id: int, doc_type: str = "invoice", confidence: float = 0.95):
    return SimpleNamespace(
        id=1,
        document_id=document_id,
        document_type=doc_type,
        confidence_score=confidence,
        extracted_data={"amount": 100.0},
        extraction_model="openai/gpt-4o-mini",
        extraction_error=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestMetadataAPI:
    """Integration tests for metadata endpoints."""

    def test_get_metadata_without_auth(self, client):
        """Test getting metadata without authentication."""
        response = client.get("/api/v1/documents/1/metadata")
        assert response.status_code == 401

    def test_get_metadata_document_not_found(self, client, logged_in_user):
        """Test getting metadata for nonexistent document."""
        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}
        response = client.get("/api/v1/documents/99999/metadata", headers=headers)
        assert response.status_code == 404

    def test_get_metadata_unauthorized(self, client, logged_in_user, test_document_other_user):
        """Test getting metadata for another user's document."""
        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}
        response = client.get(
            f"/api/v1/documents/{test_document_other_user.id}/metadata",
            headers=headers,
        )
        assert response.status_code == 404

    def test_extract_metadata_without_auth(self, client):
        """Test extracting metadata without authentication."""
        response = client.post("/api/v1/documents/1/extract-metadata")
        assert response.status_code == 401

    def test_extract_metadata_no_text(self, client, logged_in_user, test_document, db):
        """Test extracting metadata from document with no text."""
        test_document.extracted_text = None
        db.add(test_document)
        db.commit()
        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}

        response = client.post(
            f"/api/v1/documents/{test_document.id}/extract-metadata",
            headers=headers,
        )

        assert response.status_code == 422
        data = response.json()
        assert "no extracted text" in data["error"]["message"].lower()

    @patch("app.api.v1.routes.metadata.MetadataService")
    def test_extract_metadata_success(self, mock_service, client, logged_in_user, test_document, db):
        """Test successful metadata extraction."""
        mock_service_instance = Mock()
        mock_metadata = _metadata_ns(test_document.id, "invoice", 0.95)

        mock_service_instance.process_and_extract.return_value = None
        mock_service_instance.get_metadata.return_value = mock_metadata
        mock_service.return_value = mock_service_instance

        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}
        response = client.post(
            f"/api/v1/documents/{test_document.id}/extract-metadata",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["document_type"] == "invoice"

    def test_get_metadata_summary_not_extracted(self, client, logged_in_user, test_document):
        """Test getting metadata summary when none exists."""
        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}

        response = client.get(
            f"/api/v1/documents/{test_document.id}/metadata/summary",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["extracted"] is False
        assert data["data"]["document_type"] is None

    @patch("app.api.v1.routes.metadata.MetadataService")
    def test_get_metadata_summary_extracted(self, mock_service, client, logged_in_user, test_document):
        """Test getting metadata summary for extracted metadata."""
        # Setup mock
        mock_service_instance = Mock()
        mock_metadata = SimpleNamespace(
            document_type="invoice",
            confidence_score=0.92,
            extracted_data={
            "amount": 250.00,
            "currency": "USD",
            "invoice_number": "INV-123",
            "date": "2026-03-26",
            },
            extraction_error=None,
        )

        mock_service.return_value = mock_service_instance

        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}

        with patch(
            "app.api.v1.routes.metadata.MetadataRepository.get_by_document_id",
            return_value=mock_metadata,
        ):
            response = client.get(
                f"/api/v1/documents/{test_document.id}/metadata/summary",
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["document_type"] == "invoice"
        assert data["data"]["confidence"] == 0.92
        assert data["data"]["extracted"] is True
        assert data["data"]["field_count"] == 4


class TestMetadataWorkflow:
    """Tests for complete metadata extraction workflow."""

    @patch("app.services.metadata_extractor.MetadataExtractor.classify_document")
    @patch("app.services.metadata_extractor.MetadataExtractor.extract_invoice_data")
    def test_full_invoice_extraction_flow(
        self,
        mock_extract_invoice,
        mock_classify,
        client,
        logged_in_user,
        test_document,
    ):
        """Test full invoice extraction workflow."""
        # Setup test document
        from app.models.enums import DocumentStatus
        test_document.processing_status = DocumentStatus.PROCESSING
        test_document.extracted_text = "Invoice #INV-001\nAmount: $299.99\nDate: 2026-03-26"

        # Setup mocks
        mock_classify.return_value = ("invoice", 0.96)
        mock_extract_invoice.return_value = {
            "amount": 299.99,
            "currency": "USD",
            "invoice_number": "INV-001",
            "date": "2026-03-26",
        }

        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}

        with patch("app.api.v1.routes.metadata.MetadataService") as mock_service:
            mock_service_instance = Mock()
            mock_metadata = _metadata_ns(test_document.id, "invoice", 0.96)
            mock_metadata.extracted_data = {
                "amount": 299.99,
                "currency": "USD",
                "invoice_number": "INV-001",
                "date": "2026-03-26",
            }

            mock_service_instance.process_and_extract.return_value = None
            mock_service_instance.get_metadata.return_value = mock_metadata
            mock_service.return_value = mock_service_instance

            response = client.post(
                f"/api/v1/documents/{test_document.id}/extract-metadata",
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["document_type"] == "invoice"
            assert data["data"]["extracted_data"]["amount"] == 299.99

    def test_status_transitions_on_metadata_extraction(
        self, client, logged_in_user, test_document, db
    ):
        """Test status transitions during metadata extraction."""
        test_document.processing_status = DocumentStatus.PROCESSING
        test_document.extracted_text = "Sample invoice text"
        db.commit()

        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}

        with patch("app.api.v1.routes.metadata.MetadataService") as mock_service:
            mock_service_instance = Mock()
            mock_metadata = _metadata_ns(test_document.id, "invoice", 0.9)

            mock_service_instance.process_and_extract.return_value = None
            mock_service_instance.get_metadata.return_value = mock_metadata
            mock_service.return_value = mock_service_instance

            response = client.post(
                f"/api/v1/documents/{test_document.id}/extract-metadata",
                headers=headers,
            )

            assert response.status_code == 200
            # Service should have been called to process and extract
            mock_service_instance.process_and_extract.assert_called_once()
