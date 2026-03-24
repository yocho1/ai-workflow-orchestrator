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

    def list_documents(self, db: Session) -> list[Document]:
        return self.repository.list(db)

    def get_document(self, db: Session, document_id: int) -> Document:
        document = self.repository.get_by_id(db, document_id)
        if document is None:
            raise ValueError(f"Document {document_id} not found")
        return document

    def update_document(self, db: Session, document_id: int, payload: DocumentUpdate) -> Document:
        document = self.repository.get_by_id(db, document_id)
        if document is None:
            raise ValueError(f"Document {document_id} not found")

        updated = self.repository.update(db, document, payload)
        db.commit()
        return updated

    def delete_document(self, db: Session, document_id: int) -> None:
        document = self.repository.get_by_id(db, document_id)
        if document is None:
            raise ValueError(f"Document {document_id} not found")

        self.repository.delete(db, document)
        db.commit()
