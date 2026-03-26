from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import DocumentStatus
from app.models.utils import utcnow

if TYPE_CHECKING:
    from app.models.metadata import DocumentMetadata


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_status: Mapped[DocumentStatus] = mapped_column(String(50), nullable=False, default=DocumentStatus.UPLOADED)
    document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    owner: Mapped["User | None"] = relationship(back_populates="documents")
    processing_logs: Mapped[list["ProcessingLog"]] = relationship(back_populates="document")
    extracted_metadata: Mapped["DocumentMetadata | None"] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="joined",
    )
