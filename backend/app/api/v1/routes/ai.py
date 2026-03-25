from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.response import ok_response
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.ai import AskDocumentRequest
from app.services.ai_service import AiService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post(
    "/documents/{document_id}/classify",
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Document not found"}, 503: {"description": "AI provider unavailable"}},
)
def classify_document(
    document_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    service = AiService()
    try:
        result = service.classify_document(db, document_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    body = ok_response(result.model_dump(mode="json"))
    return {"success": body["success"], "data": body["data"], "error": body["error"]}


@router.post(
    "/documents/{document_id}/ask",
    status_code=status.HTTP_200_OK,
    responses={404: {"description": "Document not found"}, 503: {"description": "AI provider unavailable"}},
)
def ask_document(
    document_id: int,
    payload: AskDocumentRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    service = AiService()
    try:
        result = service.ask_document(db, document_id, payload.question, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    body = ok_response(result.model_dump())
    return {"success": body["success"], "data": body["data"], "error": body["error"]}
