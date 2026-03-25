from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.response import ok_response
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"description": "Email already registered"}},
)
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    service = AuthService()
    try:
        result = service.register(db, email=payload.email, full_name=payload.full_name, password=payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    body = ok_response(result.model_dump(mode="json"))
    return {"success": body["success"], "data": body["data"], "error": body["error"]}


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_401_UNAUTHORIZED: {"description": "Invalid credentials"}},
)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> dict:
    service = AuthService()
    try:
        result = service.login(db, email=payload.email, password=payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    body = ok_response(result.model_dump(mode="json"))
    return {"success": body["success"], "data": body["data"], "error": body["error"]}


@router.get("/me", status_code=status.HTTP_200_OK)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> dict:
    service = AuthService()
    result = service.me(current_user)
    body = ok_response(result.model_dump(mode="json"))
    return {"success": body["success"], "data": body["data"], "error": body["error"]}
