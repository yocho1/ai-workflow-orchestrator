from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentStatus


class DocumentBase(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)
    storage_path: str = Field(min_length=1, max_length=500)
    extracted_text: str | None = None
    processing_status: DocumentStatus = Field(default=DocumentStatus.UPLOADED)
    document_type: str | None = Field(default=None, max_length=100)
    user_id: int | None = None


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    filename: str | None = Field(default=None, min_length=1, max_length=255)
    content_type: str | None = Field(default=None, min_length=1, max_length=100)
    storage_path: str | None = Field(default=None, min_length=1, max_length=500)
    extracted_text: str | None = None
    processing_status: DocumentStatus | None = Field(default=None)
    document_type: str | None = Field(default=None, max_length=100)
    user_id: int | None = None


class DocumentRead(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class DocumentStatusUpdate(BaseModel):
    """Request body for status update endpoint"""

    status: DocumentStatus = Field(..., description="New status for the document")
    message: str | None = Field(
        default=None,
        max_length=500,
        description="Optional reason for status change (e.g., error message if failed)",
    )

