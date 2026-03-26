from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.response import ok_response
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentRead, DocumentStatusUpdate, DocumentUpdate
from app.services.document_service import DocumentService
from app.services.document_status_service import DocumentStatusService
from app.services.file_ingestion_service import FileIngestionService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_document(
    payload: DocumentCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    service = DocumentService()
    payload_with_owner = payload.model_copy(update={"user_id": current_user.id})
    document = service.create_document(db, payload_with_owner)
    body = ok_response(DocumentRead.model_validate(document).model_dump())
    return {"success": body["success"], "data": body["data"], "error": body["error"]}


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid upload payload"},
        413: {"description": "File too large"},
        415: {"description": "Unsupported file type"},
    },
)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    settings = get_settings()
    max_bytes = settings.upload_max_mb * 1024 * 1024

    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.upload_max_mb} MB limit")

    ingestion_service = FileIngestionService()
    try:
        storage_path, extracted_text = ingestion_service.ingest(original_filename=file.filename, content=content)
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    payload = DocumentCreate(
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        storage_path=storage_path,
        extracted_text=extracted_text,
        processing_status="uploaded",
        document_type=None,
        user_id=current_user.id,
    )

    service = DocumentService()
    document = service.create_document(db, payload)

    body = ok_response(DocumentRead.model_validate(document).model_dump())
    return {"success": body["success"], "data": body["data"], "error": body["error"]}


@router.get("", status_code=status.HTTP_200_OK)
def list_documents(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    service = DocumentService()
    documents = service.list_documents(db, current_user.id)
    data = [DocumentRead.model_validate(doc).model_dump() for doc in documents]
    body = ok_response(data)
    return {"success": body["success"], "data": body["data"], "error": body["error"]}


@router.get(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Document not found"}},
)
def get_document(
    document_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    service = DocumentService()

    try:
        document = service.get_document(db, document_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    body = ok_response(DocumentRead.model_validate(document).model_dump())
    return {"success": body["success"], "data": body["data"], "error": body["error"]}


@router.post(
    "/{document_id}/status",
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Document not found"},
        422: {"description": "Invalid status transition"},
    },
)
def update_document_status(
    document_id: int,
    payload: DocumentStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """
    Update document processing status with validation.

    Status transitions follow a state machine:
    - uploaded → processing, failed
    - processing → classified, failed
    - classified → completed, failed
    - completed → processing (allow reprocessing)
    - failed → processing (allow retry)
    """
    service = DocumentStatusService()

    try:
        document = service.update_status(
            db,
            document_id,
            payload.status,
            payload.message,
        )
        # Verify ownership
        if document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this document")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    body = ok_response(DocumentRead.model_validate(document).model_dump())
    return {"success": body["success"], "data": body["data"], "error": body["error"]}


@router.put(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Document not found"}},
)
def update_document(
    document_id: int,
    payload: DocumentUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    service = DocumentService()

    try:
        document = service.update_document(db, document_id, payload, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    body = ok_response(DocumentRead.model_validate(document).model_dump())
    return {"success": body["success"], "data": body["data"], "error": body["error"]}


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Document not found"}},
)
def delete_document(
    document_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    service = DocumentService()

    try:
        service.delete_document(db, document_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    body = ok_response({"id": document_id, "deleted": True})
    return {"success": body["success"], "data": body["data"], "error": body["error"]}
