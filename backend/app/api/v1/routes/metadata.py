"""API routes for document metadata operations."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.response import ok_response
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.metadata_repository import MetadataRepository
from app.schemas.metadata import MetadataRead
from app.services.metadata_service import MetadataService

router = APIRouter(prefix="/documents", tags=["metadata"])


@router.get("/{document_id}/metadata", response_model=MetadataRead)
def get_document_metadata(
    document_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Retrieve metadata for a document."""
    # Check ownership
    doc_repo = DocumentRepository()
    owned_document = doc_repo.get_by_id_for_user(db, document_id, current_user.id)
    if not owned_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Get metadata
    metadata_repo = MetadataRepository()
    metadata = metadata_repo.get_by_document_id(db, document_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata not found for document",
        )

    return metadata


@router.post("/{document_id}/extract-metadata")
def extract_document_metadata(
    document_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """
    Extract metadata from a document.
    
    This endpoint triggers the metadata extraction pipeline:
    1. Classify document type (invoice, contract, receipt, etc.)
    2. Extract type-specific structured data
    3. Update document status: processing → classified → completed
    """
    # Check ownership
    doc_repo = DocumentRepository()
    owned_document = doc_repo.get_by_id_for_user(db, document_id, current_user.id)
    if not owned_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if not owned_document.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Document has no extracted text",
        )

    # Process metadata
    service = MetadataService()
    service.process_and_extract(db, owned_document, owned_document.extracted_text)

    # Return updated metadata
    metadata = service.get_metadata(db, document_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract metadata",
        )

    serialized_metadata = MetadataRead.model_validate(metadata).model_dump(mode="json")
    return ok_response(serialized_metadata)


@router.get("/{document_id}/metadata/summary")
def get_metadata_summary(
    document_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Get a summary of extracted metadata for a document."""
    # Check ownership
    doc_repo = DocumentRepository()
    owned_document = doc_repo.get_by_id_for_user(db, document_id, current_user.id)
    if not owned_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Get metadata
    metadata_repo = MetadataRepository()
    metadata = metadata_repo.get_by_document_id(db, document_id)

    if not metadata:
        return {
            "success": True,
            "data": {
                "document_id": document_id,
                "document_type": None,
                "extracted": False,
            },
            "error": None,
        }

    # Create summary
    summary = {
        "document_id": document_id,
        "document_type": metadata.document_type,
        "confidence": metadata.confidence_score,
        "extracted": metadata.extraction_error is None,
        "field_count": len(metadata.extracted_data),
        "fields": list(metadata.extracted_data.keys()),
    }

    return {
        "success": True,
        "data": summary,
        "error": None,
    }
