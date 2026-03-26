from datetime import datetime

from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    document_id: int
    document_type: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    updated_at: datetime


class AskDocumentRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class AskDocumentResult(BaseModel):
    document_id: int
    question: str
    answer: str
    confidence: float | None = None
    context_chunks_used: int = 0
    used_context_chars: int
