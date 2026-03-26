"""Service for managing document metadata and triggering extraction."""

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.enums import DocumentStatus
from app.repositories.metadata_repository import MetadataRepository
from app.schemas.metadata import MetadataUpdate
from app.services.document_status_service import DocumentStatusService
from app.services.metadata_extractor import MetadataExtractor


class MetadataService:
    """Orchestrates metadata extraction and status transitions."""

    def __init__(
        self,
        extractor: MetadataExtractor | None = None,
        status_service: DocumentStatusService | None = None,
        metadata_repo: MetadataRepository | None = None,
    ) -> None:
        """Initialize service with optional dependencies."""
        self.extractor = extractor or MetadataExtractor()
        self.status_service = status_service or DocumentStatusService()
        self.metadata_repo = metadata_repo or MetadataRepository()

    def process_and_extract(
        self,
        db: Session,
        document: Document,
        extracted_text: str | None = None,
    ) -> None:
        """
        Process document for metadata extraction and update status.
        
        Flow:
        1. Extract metadata using AI
        2. Transition status: processing → classified → completed
        """
        text = extracted_text or document.extracted_text or ""

        if not text:
            # No text to process
            self.status_service.update_status(
                db,
                document.id,
                DocumentStatus.FAILED,
                "No text available for extraction",
            )
            return

        try:
            # Extract metadata
            metadata = self.extractor.extract_metadata(db, document.id, text)

            # Transition: processing → classified
            self.status_service.update_status(
                db,
                document.id,
                DocumentStatus.CLASSIFIED,
                f"Document classified as: {metadata.document_type} (confidence: {metadata.confidence_score:.2f})",
            )

            # Transition: classified → completed
            self.status_service.update_status(
                db,
                document.id,
                DocumentStatus.COMPLETED,
                "Metadata extraction complete",
            )

            db.commit()

        except Exception as e:
            # Transition to failed on error
            self.status_service.update_status(
                db,
                document.id,
                DocumentStatus.FAILED,
                f"Metadata extraction failed: {str(e)}",
            )
            db.commit()

    def get_metadata(self, db: Session, document_id: int):
        """Retrieve metadata for a document."""
        return self.metadata_repo.get_by_document_id(db, document_id)

    def update_metadata(
        self,
        db: Session,
        document_id: int,
        payload: MetadataUpdate,
    ):
        """Update metadata fields for manual human review/correction."""
        update_payload = MetadataUpdate(
            document_type=payload.document_type,
            confidence_score=payload.confidence_score,
            extracted_data=payload.extracted_data,
            needs_review=False,
            review_reason=None,
        )
        metadata = self.metadata_repo.update_by_document_id(db, document_id, update_payload)
        if metadata:
            db.commit()
        return metadata
