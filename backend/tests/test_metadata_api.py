"""Integration tests for metadata API endpoints."""

import csv
import io
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.models.document import Document
from app.models.enums import DocumentStatus
from app.repositories.metadata_repository import MetadataRepository
from app.schemas.metadata import MetadataCreate


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

    @patch("app.api.v1.routes.metadata.MetadataService")
    def test_update_metadata_success(self, mock_service, client, logged_in_user, test_document):
        """Test successful manual metadata update."""
        mock_service_instance = Mock()
        mock_service_instance.update_metadata.return_value = _metadata_ns(
            test_document.id,
            "invoice",
            0.88,
        )
        mock_service.return_value = mock_service_instance

        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}
        response = client.patch(
            f"/api/v1/documents/{test_document.id}/metadata",
            headers=headers,
            json={
                "document_type": "invoice",
                "confidence_score": 0.88,
                "extracted_data": {"amount": 123.45, "currency": "USD"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["document_id"] == test_document.id
        mock_service_instance.update_metadata.assert_called_once()

    def test_update_metadata_requires_auth(self, client):
        """Test metadata update requires authentication."""
        response = client.patch(
            "/api/v1/documents/1/metadata",
            json={"document_type": "invoice"},
        )
        assert response.status_code == 401

    def test_review_queue_returns_flagged_metadata(self, client, logged_in_user, test_document, db):
        """Review queue should contain low-confidence flagged metadata."""
        metadata_repo = MetadataRepository()
        metadata_repo.create(
            db,
            test_document.id,
            MetadataCreate(
                document_type="invoice",
                confidence_score=0.55,
                extracted_data={"amount": 42},
                needs_review=True,
                review_reason="Low confidence (0.55) below threshold (0.80)",
            ),
        )
        db.commit()

        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}
        response = client.get("/api/v1/documents/metadata/review-queue", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["document_id"] == test_document.id
        assert "Low confidence" in data["data"][0]["review_reason"]

    @patch("app.services.metadata_extractor.MetadataExtractor.classify_document", return_value=("invoice", 0.9))
    @patch("app.services.metadata_extractor.MetadataExtractor.extract_invoice_data", return_value={"amount": 100})
    def test_batch_extract_metadata_starts_job_and_completes(
        self,
        _mock_extract,
        _mock_classify,
        client,
        logged_in_user,
        test_document,
        db,
    ):
        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}

        test_document.processing_status = DocumentStatus.PROCESSING
        db.add(test_document)
        db.commit()

        start_response = client.post(
            "/api/v1/documents/batch/extract-metadata",
            headers=headers,
            json={"document_ids": [test_document.id]},
        )

        assert start_response.status_code == 202
        start_payload = start_response.json()["data"]
        assert start_payload["job_id"]

        status_response = client.get(
            f"/api/v1/jobs/{start_payload['job_id']}",
            headers=headers,
        )
        assert status_response.status_code == 200
        status_payload = status_response.json()["data"]
        assert status_payload["total_documents"] == 1
        assert status_payload["processed_documents"] == 1
        assert status_payload["success_count"] == 1

    def test_batch_extract_metadata_rejects_unowned_document(
        self,
        client,
        logged_in_user,
        test_document_other_user,
    ):
        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}

        response = client.post(
            "/api/v1/documents/batch/extract-metadata",
            headers=headers,
            json={"document_ids": [test_document_other_user.id]},
        )

        assert response.status_code == 404

    def test_get_job_status_requires_owner(self, client, logged_in_user, test_document):
        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}

        start_response = client.post(
            "/api/v1/documents/batch/extract-metadata",
            headers=headers,
            json={"document_ids": [test_document.id]},
        )
        assert start_response.status_code == 202
        job_id = start_response.json()["data"]["job_id"]

        # Create another user and ensure job is hidden.
        register = client.post(
            "/api/v1/auth/register",
            json={"email": "jobviewer@example.com", "password": "testpassword123", "full_name": "Job Viewer"},
        )
        assert register.status_code == 201
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "jobviewer@example.com", "password": "testpassword123"},
        )
        other_token = login.json()["data"]["token"]["access_token"]

        other_headers = {"Authorization": f"Bearer {other_token}"}
        status_response = client.get(f"/api/v1/jobs/{job_id}", headers=other_headers)
        assert status_response.status_code == 404

    def test_export_metadata_csv_requires_auth(self, client):
        response = client.get("/api/v1/documents/metadata/export/csv")
        assert response.status_code == 401

    def test_export_metadata_csv_success(self, client, logged_in_user, test_document, db):
        metadata_repo = MetadataRepository()
        metadata_repo.create(
            db,
            test_document.id,
            MetadataCreate(
                document_type="invoice",
                confidence_score=0.91,
                extracted_data={"amount": 199.99, "currency": "USD"},
                needs_review=False,
            ),
        )
        db.commit()

        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}
        response = client.get("/api/v1/documents/metadata/export/csv", headers=headers)

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment; filename=\"metadata_export_" in response.headers["content-disposition"]

        content = response.content.decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(content)))
        assert len(rows) >= 1
        row = next(r for r in rows if int(r["document_id"]) == test_document.id)
        assert row["filename"] == test_document.filename
        assert row["document_type"] == "invoice"
        assert row["confidence_score"] == "0.91"

    def test_export_metadata_csv_with_filters(self, client, logged_in_user, test_document, db):
        second_document = Document(
            user_id=logged_in_user["user_id"],
            filename="test_contract.pdf",
            content_type="application/pdf",
            storage_path="/uploads/test_contract.pdf",
            extracted_text="Contract text",
            processing_status=DocumentStatus.UPLOADED,
            document_type=None,
        )
        db.add(second_document)
        db.commit()
        db.refresh(second_document)

        metadata_repo = MetadataRepository()
        metadata_repo.create(
            db,
            test_document.id,
            MetadataCreate(
                document_type="invoice",
                confidence_score=0.91,
                extracted_data={"amount": 199.99},
                needs_review=True,
                review_reason="Low confidence",
            ),
        )
        metadata_repo.create(
            db,
            second_document.id,
            MetadataCreate(
                document_type="contract",
                confidence_score=0.98,
                extracted_data={"parties": ["A", "B"]},
                needs_review=False,
            ),
        )
        db.commit()

        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}
        response = client.get(
            "/api/v1/documents/metadata/export/csv?document_type=invoice&needs_review=true",
            headers=headers,
        )

        assert response.status_code == 200
        content = response.content.decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(content)))
        assert len(rows) == 1
        assert int(rows[0]["document_id"]) == test_document.id
        assert rows[0]["document_type"] == "invoice"

    def test_export_metadata_pdf_requires_auth(self, client):
        response = client.get("/api/v1/documents/metadata/export/pdf")
        assert response.status_code == 401

    def test_export_metadata_pdf_success(self, client, logged_in_user, test_document, db):
        metadata_repo = MetadataRepository()
        metadata_repo.create(
            db,
            test_document.id,
            MetadataCreate(
                document_type="invoice",
                confidence_score=0.91,
                extracted_data={"amount": 199.99, "currency": "USD"},
                needs_review=False,
            ),
        )
        db.commit()

        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}
        response = client.get("/api/v1/documents/metadata/export/pdf", headers=headers)

        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]
        assert "attachment; filename=\"metadata_export_" in response.headers["content-disposition"]
        assert response.content.startswith(b"%PDF")

    def test_export_metadata_pdf_with_filters(self, client, logged_in_user, test_document, db):
        metadata_repo = MetadataRepository()
        metadata_repo.create(
            db,
            test_document.id,
            MetadataCreate(
                document_type="invoice",
                confidence_score=0.91,
                extracted_data={"amount": 199.99},
                needs_review=False,
            ),
        )
        db.commit()

        headers = {"Authorization": f"Bearer {logged_in_user['token']}"}
        response = client.get(
            "/api/v1/documents/metadata/export/pdf?document_type=invoice&needs_review=false",
            headers=headers,
        )

        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]
        assert response.content.startswith(b"%PDF")


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
