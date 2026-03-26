"""Repository for DocumentMetadata database operations."""

from sqlalchemy.orm import Session

from app.models.metadata import DocumentMetadata
from app.schemas.metadata import MetadataCreate, MetadataUpdate


class MetadataRepository:
    """Data access layer for DocumentMetadata."""

    @staticmethod
    def get_by_document_id(db: Session, document_id: int) -> DocumentMetadata | None:
        """Get metadata by document ID."""
        return db.query(DocumentMetadata).filter(DocumentMetadata.document_id == document_id).first()

    @staticmethod
    def create(
        db: Session,
        document_id: int,
        payload: MetadataCreate,
    ) -> DocumentMetadata:
        """Create new metadata record."""
        metadata = DocumentMetadata(
            document_id=document_id,
            document_type=payload.document_type,
            confidence_score=payload.confidence_score,
            extracted_data=payload.extracted_data,
            extraction_model=payload.extraction_model,
            extraction_error=payload.extraction_error,
        )
        db.add(metadata)
        db.flush()
        return metadata

    @staticmethod
    def update(
        db: Session,
        metadata_id: int,
        payload: MetadataUpdate,
    ) -> DocumentMetadata | None:
        """Update existing metadata record."""
        metadata = db.query(DocumentMetadata).filter(DocumentMetadata.id == metadata_id).first()
        if not metadata:
            return None

        if payload.document_type is not None:
            metadata.document_type = payload.document_type
        if payload.confidence_score is not None:
            metadata.confidence_score = payload.confidence_score
        if payload.extracted_data is not None:
            metadata.extracted_data = payload.extracted_data

        db.flush()
        return metadata

    @staticmethod
    def delete(db: Session, metadata_id: int) -> bool:
        """Delete metadata record."""
        metadata = db.query(DocumentMetadata).filter(DocumentMetadata.id == metadata_id).first()
        if not metadata:
            return False

        db.delete(metadata)
        db.flush()
        return True

    @staticmethod
    def update_by_document_id(
        db: Session,
        document_id: int,
        payload: MetadataUpdate,
    ) -> DocumentMetadata | None:
        """Update metadata by document ID."""
        metadata = MetadataRepository.get_by_document_id(db, document_id)
        if not metadata:
            return None

        return MetadataRepository.update(db, metadata.id, payload)
