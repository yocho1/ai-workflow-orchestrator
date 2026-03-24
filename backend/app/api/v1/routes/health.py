from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.response import ok_response
from app.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", status_code=200)
def health_check(db: Annotated[Session, Depends(get_db)]) -> dict:
    service = HealthService()
    data = service.get_health_status(db)
    response = ok_response(data=data)
    return {
        "success": response["success"],
        "data": response["data"],
        "error": response["error"],
    }
