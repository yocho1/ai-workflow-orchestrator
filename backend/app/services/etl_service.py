from sqlalchemy.orm import Session

from app.models.document import Document
from app.pipelines.document_etl_pipeline import DocumentEtlPipeline
from app.repositories.document_repository import DocumentRepository
from app.repositories.processing_log_repository import ProcessingLogRepository
from app.schemas.etl import DocumentEtlResult, EtlLogEntry


class EtlService:
    def __init__(
        self,
        document_repository: DocumentRepository | None = None,
        log_repository: ProcessingLogRepository | None = None,
        pipeline: DocumentEtlPipeline | None = None,
    ) -> None:
        self.document_repository = document_repository or DocumentRepository()
        self.log_repository = log_repository or ProcessingLogRepository()
        self.pipeline = pipeline or DocumentEtlPipeline()

    def run_document_etl(self, db: Session, document_id: int) -> DocumentEtlResult:
        document = self.document_repository.get_by_id(db, document_id)
        if document is None:
            raise ValueError(f"Document {document_id} not found")

        document.processing_status = "processing"

        self.log_repository.create(
            db,
            document_id=document.id,
            pipeline_step="extract",
            status="started",
            message="Starting extraction step",
        )
        extracted = self.pipeline.extract(document)
        self.log_repository.create(
            db,
            document_id=document.id,
            pipeline_step="extract",
            status="completed",
            message=f"Extracted {len(extracted)} characters",
        )

        self.log_repository.create(
            db,
            document_id=document.id,
            pipeline_step="transform",
            status="started",
            message="Starting normalization and classification",
        )
        normalized, inferred_type = self.pipeline.transform(extracted)
        self.log_repository.create(
            db,
            document_id=document.id,
            pipeline_step="transform",
            status="completed",
            message=f"Inferred type: {inferred_type or 'unknown'}",
        )

        self.log_repository.create(
            db,
            document_id=document.id,
            pipeline_step="load",
            status="started",
            message="Applying ETL output to document",
        )
        self.pipeline.load(document, normalized_text=normalized, inferred_type=inferred_type)
        self.log_repository.create(
            db,
            document_id=document.id,
            pipeline_step="load",
            status="completed",
            message="Document fields updated",
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        logs = self.log_repository.list_by_document(db, document.id)
        return self._to_result(document, logs)

    def run_pending_documents(self, db: Session) -> list[int]:
        pending_docs = [
            d
            for d in self.document_repository.list(db)
            if d.processing_status in {"uploaded", "processing"}
        ]

        processed_ids: list[int] = []
        for document in pending_docs:
            self.run_document_etl(db, document.id)
            processed_ids.append(document.id)

        return processed_ids

    def _to_result(self, document: Document, logs: list) -> DocumentEtlResult:
        return DocumentEtlResult(
            document_id=document.id,
            processing_status=document.processing_status,
            document_type=document.document_type,
            extracted_text_preview=(document.extracted_text or "")[:200] or None,
            logs=[
                EtlLogEntry(
                    pipeline_step=entry.pipeline_step,
                    status=entry.status,
                    message=entry.message,
                    created_at=entry.created_at,
                )
                for entry in logs
            ],
        )
