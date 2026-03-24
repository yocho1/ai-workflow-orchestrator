from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)
    storage_path: str = Field(min_length=1, max_length=500)
    extracted_text: str | None = None
    processing_status: str = Field(default="uploaded", max_length=50)
    document_type: str | None = Field(default=None, max_length=100)
    user_id: int | None = None


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    filename: str | None = Field(default=None, min_length=1, max_length=255)
    content_type: str | None = Field(default=None, min_length=1, max_length=100)
    storage_path: str | None = Field(default=None, min_length=1, max_length=500)
    extracted_text: str | None = None
    processing_status: str | None = Field(default=None, max_length=50)
    document_type: str | None = Field(default=None, max_length=100)
    user_id: int | None = None


class DocumentRead(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
