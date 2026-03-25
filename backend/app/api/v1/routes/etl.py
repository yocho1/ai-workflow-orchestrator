from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.response import ok_response
from app.schemas.etl import RunPendingDocumentsResponse
from app.services.etl_service import EtlService

router = APIRouter(prefix="/etl", tags=["etl"])


@router.post("/documents/{document_id}/run", status_code=status.HTTP_200_OK)
def run_document_etl(document_id: int, db: Annotated[Session, Depends(get_db)]) -> dict:
    service = EtlService()
    try:
        result = service.run_document_etl(db, document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    body = ok_response(result.model_dump(mode="json"))
    return {"success": body["success"], "data": body["data"], "error": body["error"]}


@router.post("/documents/run-pending", status_code=status.HTTP_200_OK)
def run_pending_documents_etl(db: Annotated[Session, Depends(get_db)]) -> dict:
    service = EtlService()
    processed_ids = service.run_pending_documents(db)
    payload = RunPendingDocumentsResponse(processed=len(processed_ids), document_ids=processed_ids)
    body = ok_response(payload.model_dump())
    return {"success": body["success"], "data": body["data"], "error": body["error"]}
