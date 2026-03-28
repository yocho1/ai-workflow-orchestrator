from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.response import ok_response
from app.core.security import get_current_user
from app.models.user import User
from app.services.batch_extraction_jobs import BatchExtractionJobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", status_code=status.HTTP_200_OK)
def get_job_status(
    job_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    service = BatchExtractionJobService()
    job = service.get_job(job_id=job_id, user_id=current_user.id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    payload = service.to_response(job)
    body = ok_response(payload.model_dump(mode="json"))
    return {"success": body["success"], "data": body["data"], "error": body["error"]}
