"""API routes for document metadata operations."""

import csv
import io
import json
from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.core.response import ok_response
from app.core.db import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.metadata_repository import MetadataRepository
from app.schemas.jobs import BatchExtractRequest, BatchExtractStartResponse
from app.schemas.metadata import MetadataRead, MetadataReviewQueueItem, MetadataUpdate
from app.services.batch_extraction_jobs import BatchExtractionJobService
from app.services.metadata_service import MetadataService

router = APIRouter(prefix="/documents", tags=["metadata"])


def _draw_wrapped_lines(pdf: canvas.Canvas, text: str, x: int, y: int, max_width: int, line_height: int) -> int:
    """Draw wrapped text and return updated y coordinate."""
    current = ""
    words = text.split(" ")

    for word in words:
        candidate = f"{current} {word}".strip()
        if pdf.stringWidth(candidate, "Helvetica", 10) <= max_width:
            current = candidate
            continue

        if current:
            pdf.drawString(x, y, current)
            y -= line_height
        current = word

    if current:
        pdf.drawString(x, y, current)
        y -= line_height

    return y


def _record_updated_date(document) -> date:
    metadata = document.extracted_metadata
    if metadata and metadata.updated_at:
        return metadata.updated_at.date()
    return document.updated_at.date()


def _filter_export_documents(
    documents,
    document_type: str | None,
    needs_review: bool | None,
    updated_from: date | None,
    updated_to: date | None,
):
    filtered = []
    for document in documents:
        metadata = document.extracted_metadata

        if document_type and (not metadata or metadata.document_type != document_type):
            continue

        if needs_review is not None and (not metadata or metadata.needs_review != needs_review):
            continue

        record_date = _record_updated_date(document)
        if updated_from and record_date < updated_from:
            continue
        if updated_to and record_date > updated_to:
            continue

        filtered.append(document)

    return filtered


@router.get("/metadata/export/csv")
def export_metadata_csv(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    document_type: str | None = None,
    needs_review: bool | None = None,
    updated_from: date | None = None,
    updated_to: date | None = None,
):
    """Export all user documents with metadata as CSV."""
    doc_repo = DocumentRepository()
    documents = doc_repo.list_by_user(db, current_user.id)
    documents = _filter_export_documents(
        documents,
        document_type=document_type,
        needs_review=needs_review,
        updated_from=updated_from,
        updated_to=updated_to,
    )

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "document_id",
            "filename",
            "processing_status",
            "document_type",
            "confidence_score",
            "needs_review",
            "review_reason",
            "extraction_error",
            "extracted_data_json",
            "updated_at",
        ],
    )
    writer.writeheader()

    for document in documents:
        metadata = document.extracted_metadata
        writer.writerow(
            {
                "document_id": document.id,
                "filename": document.filename,
                "processing_status": str(document.processing_status),
                "document_type": metadata.document_type if metadata else "",
                "confidence_score": metadata.confidence_score if metadata else "",
                "needs_review": metadata.needs_review if metadata else "",
                "review_reason": metadata.review_reason if metadata else "",
                "extraction_error": metadata.extraction_error if metadata else "",
                "extracted_data_json": json.dumps(
                    metadata.extracted_data if metadata else {},
                    ensure_ascii=False,
                ),
                "updated_at": (
                    metadata.updated_at.isoformat() if metadata and metadata.updated_at else document.updated_at.isoformat()
                ),
            }
        )

    output.seek(0)
    filename = f"metadata_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

    # Prefix BOM for better compatibility with spreadsheet tools.
    csv_content = "\ufeff" + output.getvalue()
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )


@router.get("/metadata/export/pdf")
def export_metadata_pdf(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    document_type: str | None = None,
    needs_review: bool | None = None,
    updated_from: date | None = None,
    updated_to: date | None = None,
):
    """Export all user documents with metadata as a PDF report."""
    doc_repo = DocumentRepository()
    documents = doc_repo.list_by_user(db, current_user.id)
    documents = _filter_export_documents(
        documents,
        document_type=document_type,
        needs_review=needs_review,
        updated_from=updated_from,
        updated_to=updated_to,
    )

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    page_width, page_height = A4
    margin_x = 36
    top_y = page_height - 48
    line_height = 14
    content_width = int(page_width - (margin_x * 2))

    pdf.setTitle("Metadata Export")
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(margin_x, top_y, "Metadata Export")
    pdf.setFont("Helvetica", 10)
    y = top_y - 20
    y = _draw_wrapped_lines(
        pdf,
        f"Generated at {datetime.now(timezone.utc).isoformat()} | Documents: {len(documents)}",
        margin_x,
        y,
        content_width,
        line_height,
    )
    y -= 8

    for index, document in enumerate(documents, start=1):
        metadata = document.extracted_metadata

        block_lines = [
            f"{index}. Document #{document.id} - {document.filename}",
            f"Status: {document.processing_status}",
            f"Type: {metadata.document_type if metadata else '-'}",
            f"Confidence: {metadata.confidence_score if metadata else '-'}",
            f"Needs review: {metadata.needs_review if metadata else '-'}",
            f"Review reason: {metadata.review_reason if metadata and metadata.review_reason else '-'}",
            f"Extraction error: {metadata.extraction_error if metadata and metadata.extraction_error else '-'}",
            "Extracted data JSON:",
            json.dumps(metadata.extracted_data if metadata else {}, ensure_ascii=False),
        ]

        estimated_height = (len(block_lines) + 2) * line_height
        if y - estimated_height < 48:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = top_y

        pdf.setFont("Helvetica-Bold", 10)
        y = _draw_wrapped_lines(pdf, block_lines[0], margin_x, y, content_width, line_height)
        pdf.setFont("Helvetica", 10)
        for line in block_lines[1:]:
            y = _draw_wrapped_lines(pdf, line, margin_x, y, content_width, line_height)

        y -= 10

    pdf.save()
    buffer.seek(0)
    filename = f"metadata_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers=headers,
    )


@router.get("/metadata/review-queue")
def get_metadata_review_queue(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """List documents with metadata flagged for manual review."""
    doc_repo = DocumentRepository()
    documents = doc_repo.list_by_user(db, current_user.id)

    queue_items: list[dict] = []
    for document in documents:
        metadata = document.extracted_metadata
        if not metadata or not metadata.needs_review:
            continue

        item = MetadataReviewQueueItem(
            document_id=document.id,
            filename=document.filename,
            document_type=metadata.document_type,
            confidence_score=metadata.confidence_score,
            review_reason=metadata.review_reason,
            updated_at=metadata.updated_at,
        )
        queue_items.append(item.model_dump(mode="json"))

    return ok_response(queue_items)


@router.post("/metadata/batch/extract-metadata", status_code=status.HTTP_202_ACCEPTED)
@router.post("/batch/extract-metadata", status_code=status.HTTP_202_ACCEPTED)
def batch_extract_metadata(
    payload: BatchExtractRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Create and execute a background job that extracts metadata for multiple documents."""
    doc_repo = DocumentRepository()
    owned_documents = doc_repo.list_by_user(db, current_user.id)
    owned_ids = {doc.id for doc in owned_documents}
    requested_ids = list(dict.fromkeys(payload.document_ids))

    invalid_ids = [doc_id for doc_id in requested_ids if doc_id not in owned_ids]
    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documents not found or unauthorized: {invalid_ids}",
        )

    service = BatchExtractionJobService()
    job = service.create_job(user_id=current_user.id, document_ids=requested_ids)
    service.run_job(job_id=job.job_id, db=db)

    response = BatchExtractStartResponse(
        job_id=job.job_id,
        status=job.status,
        total_documents=len(requested_ids),
    )
    body = ok_response(response.model_dump(mode="json"))
    return {"success": body["success"], "data": body["data"], "error": body["error"]}


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


@router.patch("/{document_id}/metadata")
def update_document_metadata(
    document_id: int,
    payload: MetadataUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Manually review and update extracted metadata for a document."""
    doc_repo = DocumentRepository()
    owned_document = doc_repo.get_by_id_for_user(db, document_id, current_user.id)
    if not owned_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    service = MetadataService()
    updated = service.update_metadata(db, document_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metadata not found for document",
        )

    serialized_metadata = MetadataRead.model_validate(updated).model_dump(mode="json")
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
