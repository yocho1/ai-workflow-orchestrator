from datetime import datetime

from pydantic import BaseModel


class EtlLogEntry(BaseModel):
    pipeline_step: str
    status: str
    message: str | None = None
    created_at: datetime


class DocumentEtlResult(BaseModel):
    document_id: int
    processing_status: str
    document_type: str | None = None
    extracted_text_preview: str | None = None
    logs: list[EtlLogEntry]


class RunPendingDocumentsResponse(BaseModel):
    processed: int
    document_ids: list[int]
