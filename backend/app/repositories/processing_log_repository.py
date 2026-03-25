from sqlalchemy.orm import Session

from app.models.processing_log import ProcessingLog


class ProcessingLogRepository:
    def create(
        self,
        db: Session,
        *,
        pipeline_step: str,
        status: str,
        message: str | None = None,
        document_id: int | None = None,
        email_id: int | None = None,
    ) -> ProcessingLog:
        log = ProcessingLog(
            pipeline_step=pipeline_step,
            status=status,
            message=message,
            document_id=document_id,
            email_id=email_id,
        )
        db.add(log)
        db.flush()
        db.refresh(log)
        return log

    def list_by_document(self, db: Session, document_id: int) -> list[ProcessingLog]:
        return (
            db.query(ProcessingLog)
            .filter(ProcessingLog.document_id == document_id)
            .order_by(ProcessingLog.created_at.asc(), ProcessingLog.id.asc())
            .all()
        )
