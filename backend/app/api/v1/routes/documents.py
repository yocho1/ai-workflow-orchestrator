from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.response import ok_response
from app.schemas.document import DocumentCreate, DocumentRead, DocumentUpdate
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_document(
    payload: DocumentCreate,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    service = DocumentService()
    document = service.create_document(db, payload)
    body = ok_response(DocumentRead.model_validate(document).model_dump())
    return {"success": body["success"], "data": body["data"], "error": body["error"]}


@router.get("", status_code=status.HTTP_200_OK)
def list_documents(db: Annotated[Session, Depends(get_db)]) -> dict:
    service = DocumentService()
    documents = service.list_documents(db)
    data = [DocumentRead.model_validate(doc).model_dump() for doc in documents]
    body = ok_response(data)
    return {"success": body["success"], "data": body["data"], "error": body["error"]}


@router.get(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Document not found"}},
)
def get_document(document_id: int, db: Annotated[Session, Depends(get_db)]) -> dict:
    service = DocumentService()

    try:
        document = service.get_document(db, document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

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
) -> dict:
    service = DocumentService()

    try:
        document = service.update_document(db, document_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    body = ok_response(DocumentRead.model_validate(document).model_dump())
    return {"success": body["success"], "data": body["data"], "error": body["error"]}


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Document not found"}},
)
def delete_document(document_id: int, db: Annotated[Session, Depends(get_db)]) -> dict:
    service = DocumentService()

    try:
        service.delete_document(db, document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    body = ok_response({"id": document_id, "deleted": True})
    return {"success": body["success"], "data": body["data"], "error": body["error"]}
