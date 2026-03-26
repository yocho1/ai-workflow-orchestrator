"""Pydantic schemas for document metadata."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MetadataBase(BaseModel):
    """Base metadata schema."""

    document_type: str = Field(..., description="Classified document type")
    confidence_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Classification confidence (0-1)"
    )
    extracted_data: dict[str, Any] = Field(default={}, description="Extracted structured data")


class MetadataCreate(MetadataBase):
    """Metadata creation schema."""

    extraction_model: str = Field(default="openai/gpt-4o-mini", description="Model used for extraction")
    extraction_error: str | None = Field(default=None, description="Error message if extraction failed")


class MetadataUpdate(BaseModel):
    """Metadata update schema (partial)."""

    document_type: str | None = Field(default=None, description="Classified document type")
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0, description="Classification confidence")
    extracted_data: dict[str, Any] | None = Field(default=None, description="Extracted structured data")


class MetadataRead(MetadataBase):
    """Metadata read schema (response)."""

    id: int
    document_id: int
    extraction_model: str
    extraction_error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
