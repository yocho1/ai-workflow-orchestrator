from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.enums import DocumentStatus, VALID_STATUS_TRANSITIONS
from app.repositories.document_repository import DocumentRepository
from app.repositories.processing_log_repository import ProcessingLogRepository


class DocumentStatusService:
    """Service for managing document status lifecycle and validating transitions."""

    def __init__(
        self,
        document_repository: DocumentRepository | None = None,
        log_repository: ProcessingLogRepository | None = None,
    ) -> None:
        self.document_repository = document_repository or DocumentRepository()
        self.log_repository = log_repository or ProcessingLogRepository()

    def validate_transition(self, current_status: DocumentStatus, new_status: DocumentStatus) -> bool:
        """
        Validate if a status transition is allowed.

        Args:
            current_status: Current document status
            new_status: Desired new status

        Returns:
            True if transition is valid, False otherwise

        Raises:
            ValueError: If transition is invalid (with descriptive message)
        """
        if current_status == new_status:
            raise ValueError(f"Document is already in status '{current_status}'")

        allowed_transitions = VALID_STATUS_TRANSITIONS.get(current_status, [])
        if new_status not in allowed_transitions:
            raise ValueError(
                f"Cannot transition from '{current_status}' to '{new_status}'. "
                f"Allowed transitions are: {', '.join(str(s) for s in allowed_transitions)}"
            )

        return True

    def update_status(
        self,
        db: Session,
        document_id: int,
        new_status: DocumentStatus,
        message: str | None = None,
    ) -> Document:
        """
        Update document status with validation and logging.

        Args:
            db: Database session
            document_id: ID of document to update
            new_status: New status
            message: Optional message explaining the status change

        Returns:
            Updated Document instance

        Raises:
            ValueError: If document not found or transition is invalid
        """
        document = self.document_repository.get_by_id(db, document_id)
        if document is None:
            raise ValueError(f"Document {document_id} not found")

        # Validate transition
        self.validate_transition(current_status=document.processing_status, new_status=new_status)

        # Update status
        old_status = document.processing_status
        document.processing_status = new_status
        db.add(document)
        db.flush()

        # Log the transition
        log_message = message or f"Status transition: {old_status} → {new_status}"
        self.log_repository.create(
            db,
            document_id=document.id,
            pipeline_step="lifecycle_management",
            status="completed",
            message=log_message,
        )

        db.commit()
        db.refresh(document)

        return document

    def get_valid_next_statuses(self, current_status: DocumentStatus) -> list[DocumentStatus]:
        """Get list of valid next statuses for a given status."""
        return VALID_STATUS_TRANSITIONS.get(current_status, [])
