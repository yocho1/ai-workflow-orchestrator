"""
Metadata models for extracted document data.

Stores structured data extracted from documents like invoice amounts,
contract clauses, dates, etc. Linked 1:1 to Document.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.utils import utcnow


class DocumentMetadata(Base):
    """Extracted structured data from a document."""

    __tablename__ = "document_metadata"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    
    # Document classification
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_score: Mapped[float] = mapped_column(default=0.0, nullable=False)
    
    # Extracted fields (JSON for flexibility, can hold type-specific data)
    # Structure depends on document_type:
    # - invoice: {amount, currency, date, vendor, invoice_number, due_date, line_items}
    # - contract: {parties, start_date, end_date, key_clauses, expiration_date}
    # - receipt: {amount, currency, date, merchant, items}
    extracted_data: Mapped[dict[str, Any]] = mapped_column(JSON, default={}, nullable=False)
    
    # Audit fields
    extraction_model: Mapped[str] = mapped_column(
        String(100), default="openai/gpt-4o-mini", nullable=False
    )
    extraction_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # Relationship
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="extracted_metadata",
        foreign_keys=[document_id],
        cascade="all, delete-orphan",
        single_parent=True,
    )

    def __repr__(self) -> str:
        return f"<DocumentMetadata(id={self.id}, document_id={self.document_id}, type={self.document_type})>"
