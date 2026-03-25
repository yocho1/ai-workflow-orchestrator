from typing import List

from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate


class DocumentRepository:
    def create(self, db: Session, payload: DocumentCreate) -> Document:
        document = Document(**payload.model_dump())
        db.add(document)
        db.flush()
        db.refresh(document)
        return document

    def list(self, db: Session) -> List[Document]:
        return db.query(Document).order_by(Document.created_at.desc()).all()

    def list_by_user(self, db: Session, user_id: int) -> List[Document]:
        return (
            db.query(Document)
            .filter(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .all()
        )

    def get_by_id(self, db: Session, document_id: int) -> Document | None:
        return db.query(Document).filter(Document.id == document_id).first()

    def get_by_id_for_user(self, db: Session, document_id: int, user_id: int) -> Document | None:
        return (
            db.query(Document)
            .filter(Document.id == document_id, Document.user_id == user_id)
            .first()
        )

    def update(self, db: Session, document: Document, payload: DocumentUpdate) -> Document:
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(document, key, value)

        db.add(document)
        db.flush()
        db.refresh(document)
        return document

    def delete(self, db: Session, document: Document) -> None:
        db.delete(document)
        db.flush()
