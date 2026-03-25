from sqlalchemy.orm import Session

from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentCreate, DocumentUpdate


class DocumentService:
    def __init__(self, repository: DocumentRepository | None = None) -> None:
        self.repository = repository or DocumentRepository()

    def create_document(self, db: Session, payload: DocumentCreate) -> Document:
        document = self.repository.create(db, payload)
        db.commit()
        return document

    def list_documents(self, db: Session, user_id: int) -> list[Document]:
        return self.repository.list_by_user(db, user_id)

    def get_document(self, db: Session, document_id: int, user_id: int) -> Document:
        document = self.repository.get_by_id_for_user(db, document_id, user_id)
        if document is None:
            raise ValueError(f"Document {document_id} not found")
        return document

    def update_document(self, db: Session, document_id: int, payload: DocumentUpdate, user_id: int) -> Document:
        document = self.repository.get_by_id_for_user(db, document_id, user_id)
        if document is None:
            raise ValueError(f"Document {document_id} not found")

        updated = self.repository.update(db, document, payload)
        db.commit()
        return updated

    def delete_document(self, db: Session, document_id: int, user_id: int) -> None:
        document = self.repository.get_by_id_for_user(db, document_id, user_id)
        if document is None:
            raise ValueError(f"Document {document_id} not found")

        self.repository.delete(db, document)
        db.commit()
