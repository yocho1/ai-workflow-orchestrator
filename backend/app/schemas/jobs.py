from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


JobStatus = Literal["pending", "running", "completed", "failed"]


class BatchExtractRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    document_ids: list[int] = Field(default_factory=list, min_length=1)

    @model_validator(mode="before")
    @classmethod
    def _normalize_document_ids(cls, data):
        if isinstance(data, dict) and "document_ids" not in data and "documentIds" in data:
            normalized = dict(data)
            normalized["document_ids"] = normalized["documentIds"]
            return normalized
        return data


class BatchExtractStartResponse(BaseModel):
    job_id: str
    status: JobStatus
    total_documents: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    total_documents: int
    processed_documents: int
    success_count: int
    failure_count: int
    progress_percent: float = Field(ge=0.0, le=100.0)
    started_at: datetime
    finished_at: datetime | None = None
    error: str | None = None
