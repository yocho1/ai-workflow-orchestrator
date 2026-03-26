import pytest
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.enums import DocumentStatus
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.processing_log_repository import ProcessingLogRepository
from app.schemas.document import DocumentCreate
from app.services.document_status_service import DocumentStatusService


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        full_name="Test User",
        password_hash="hashed_test_password",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_document(db: Session, test_user: User) -> Document:
    """Create a test document."""
    doc_repo = DocumentRepository()
    payload = DocumentCreate(
        filename="test.txt",
        content_type="text/plain",
        storage_path="/uploads/test.txt",
        extracted_text="Test content",
        processing_status=DocumentStatus.UPLOADED,
        user_id=test_user.id,
    )
    return doc_repo.create(db, payload)


class TestDocumentStatusService:
    """Test suite for DocumentStatusService status transitions."""

    def test_valid_transition_uploaded_to_processing(self, db: Session, test_document: Document):
        """Test valid transition: uploaded → processing"""
        service = DocumentStatusService()
        updated_doc = service.update_status(db, test_document.id, DocumentStatus.PROCESSING)

        assert updated_doc.processing_status == DocumentStatus.PROCESSING
        db.refresh(updated_doc)
        assert updated_doc.processing_status == DocumentStatus.PROCESSING

    def test_valid_transition_uploaded_to_failed(self, db: Session, test_document: Document):
        """Test valid transition: uploaded → failed"""
        service = DocumentStatusService()
        updated_doc = service.update_status(
            db, test_document.id, DocumentStatus.FAILED, message="Upload failed"
        )

        assert updated_doc.processing_status == DocumentStatus.FAILED

    def test_valid_transition_processing_to_classified(self, db: Session, test_document: Document):
        """Test valid transition: processing → classified"""
        doc_repo = DocumentRepository()
        test_document.processing_status = DocumentStatus.PROCESSING
        db.add(test_document)
        db.commit()

        service = DocumentStatusService()
        updated_doc = service.update_status(db, test_document.id, DocumentStatus.CLASSIFIED)

        assert updated_doc.processing_status == DocumentStatus.CLASSIFIED

    def test_valid_transition_processing_to_failed(self, db: Session, test_document: Document):
        """Test valid transition: processing → failed"""
        test_document.processing_status = DocumentStatus.PROCESSING
        db.add(test_document)
        db.commit()

        service = DocumentStatusService()
        updated_doc = service.update_status(db, test_document.id, DocumentStatus.FAILED)

        assert updated_doc.processing_status == DocumentStatus.FAILED

    def test_valid_transition_classified_to_completed(self, db: Session, test_document: Document):
        """Test valid transition: classified → completed"""
        test_document.processing_status = DocumentStatus.CLASSIFIED
        db.add(test_document)
        db.commit()

        service = DocumentStatusService()
        updated_doc = service.update_status(db, test_document.id, DocumentStatus.COMPLETED)

        assert updated_doc.processing_status == DocumentStatus.COMPLETED

    def test_valid_transition_completed_to_processing(self, db: Session, test_document: Document):
        """Test valid transition: completed → processing (reprocessing)"""
        test_document.processing_status = DocumentStatus.COMPLETED
        db.add(test_document)
        db.commit()

        service = DocumentStatusService()
        updated_doc = service.update_status(db, test_document.id, DocumentStatus.PROCESSING)

        assert updated_doc.processing_status == DocumentStatus.PROCESSING

    def test_valid_transition_failed_to_processing(self, db: Session, test_document: Document):
        """Test valid transition: failed → processing (retry)"""
        test_document.processing_status = DocumentStatus.FAILED
        db.add(test_document)
        db.commit()

        service = DocumentStatusService()
        updated_doc = service.update_status(db, test_document.id, DocumentStatus.PROCESSING)

        assert updated_doc.processing_status == DocumentStatus.PROCESSING

    def test_invalid_transition_uploaded_to_classified(self, db: Session, test_document: Document):
        """Test invalid transition: uploaded → classified (should fail)"""
        service = DocumentStatusService()

        with pytest.raises(ValueError, match="Cannot transition"):
            service.update_status(db, test_document.id, DocumentStatus.CLASSIFIED)

    def test_invalid_transition_uploaded_to_completed(self, db: Session, test_document: Document):
        """Test invalid transition: uploaded → completed (should fail)"""
        service = DocumentStatusService()

        with pytest.raises(ValueError, match="Cannot transition"):
            service.update_status(db, test_document.id, DocumentStatus.COMPLETED)

    def test_invalid_transition_processing_to_processing(self, db: Session, test_document: Document):
        """Test invalid transition: same status (should fail)"""
        test_document.processing_status = DocumentStatus.PROCESSING
        db.add(test_document)
        db.commit()

        service = DocumentStatusService()

        with pytest.raises(ValueError, match="already in status"):
            service.update_status(db, test_document.id, DocumentStatus.PROCESSING)

    def test_invalid_transition_classified_to_processing(self, db: Session, test_document: Document):
        """Test invalid transition: classified → processing (should fail)"""
        test_document.processing_status = DocumentStatus.CLASSIFIED
        db.add(test_document)
        db.commit()

        service = DocumentStatusService()

        with pytest.raises(ValueError, match="Cannot transition"):
            service.update_status(db, test_document.id, DocumentStatus.PROCESSING)

    def test_document_not_found(self, db: Session):
        """Test update_status with non-existent document"""
        service = DocumentStatusService()

        with pytest.raises(ValueError, match="not found"):
            service.update_status(db, 9999, DocumentStatus.PROCESSING)

    def test_status_update_creates_log(self, db: Session, test_document: Document):
        """Test that status update creates a processing log entry"""
        service = DocumentStatusService()
        service.update_status(db, test_document.id, DocumentStatus.PROCESSING)

        log_repo = ProcessingLogRepository()
        logs = log_repo.list_by_document(db, test_document.id)

        assert len(logs) >= 1
        latest_log = logs[-1]
        assert latest_log.pipeline_step == "lifecycle_management"
        assert latest_log.status == "completed"
        message = (latest_log.message or "").lower()
        assert "uploaded" in message and "processing" in message

    def test_status_update_with_custom_message(self, db: Session, test_document: Document):
        """Test status update with custom message"""
        service = DocumentStatusService()
        custom_msg = "Custom failure reason"
        service.update_status(db, test_document.id, DocumentStatus.FAILED, message=custom_msg)

        log_repo = ProcessingLogRepository()
        logs = log_repo.list_by_document(db, test_document.id)

        assert custom_msg in logs[-1].message

    def test_get_valid_next_statuses(self):
        """Test get_valid_next_statuses returns correct transitions"""
        service = DocumentStatusService()

        uploaded_next = service.get_valid_next_statuses(DocumentStatus.UPLOADED)
        assert DocumentStatus.PROCESSING in uploaded_next
        assert DocumentStatus.FAILED in uploaded_next
        assert DocumentStatus.CLASSIFIED not in uploaded_next

        processing_next = service.get_valid_next_statuses(DocumentStatus.PROCESSING)
        assert DocumentStatus.CLASSIFIED in processing_next
        assert DocumentStatus.FAILED in processing_next

        completed_next = service.get_valid_next_statuses(DocumentStatus.COMPLETED)
        assert DocumentStatus.PROCESSING in completed_next
        assert DocumentStatus.CLASSIFIED not in completed_next

    def test_full_lifecycle_happy_path(self, db: Session, test_document: Document):
        """Test complete document processing lifecycle"""
        service = DocumentStatusService()

        # uploaded → processing
        doc = service.update_status(db, test_document.id, DocumentStatus.PROCESSING)
        assert doc.processing_status == DocumentStatus.PROCESSING

        # processing → classified
        db.refresh(doc)
        doc = service.update_status(db, doc.id, DocumentStatus.CLASSIFIED)
        assert doc.processing_status == DocumentStatus.CLASSIFIED

        # classified → completed
        db.refresh(doc)
        doc = service.update_status(db, doc.id, DocumentStatus.COMPLETED)
        assert doc.processing_status == DocumentStatus.COMPLETED

        # Verify order from logs
        log_repo = ProcessingLogRepository()
        logs = log_repo.list_by_document(db, doc.id)
        assert len(logs) == 3

    def test_lifecycle_with_failure_and_retry(self, db: Session, test_document: Document):
        """Test document lifecycle with failure and retry"""
        service = DocumentStatusService()

        # uploaded → processing
        doc = service.update_status(db, test_document.id, DocumentStatus.PROCESSING)

        # processing → failed
        db.refresh(doc)
        doc = service.update_status(
            db, doc.id, DocumentStatus.FAILED, message="Error during processing"
        )
        assert doc.processing_status == DocumentStatus.FAILED

        # failed → processing (retry)
        db.refresh(doc)
        doc = service.update_status(db, doc.id, DocumentStatus.PROCESSING)
        assert doc.processing_status == DocumentStatus.PROCESSING

        # Verify logs
        log_repo = ProcessingLogRepository()
        logs = log_repo.list_by_document(db, doc.id)
        assert len(logs) == 3
