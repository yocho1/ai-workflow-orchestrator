from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

from app.models.enums import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.schemas.jobs import JobStatusResponse
from app.services.metadata_service import MetadataService


@dataclass
class _JobState:
    job_id: str
    user_id: int
    document_ids: list[int]
    status: str = "pending"
    processed_documents: int = 0
    success_count: int = 0
    failure_count: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    error: str | None = None


class BatchExtractionJobService:
    _jobs: dict[str, _JobState] = {}
    _lock: Lock = Lock()

    def create_job(self, *, user_id: int, document_ids: list[int]) -> _JobState:
        job = _JobState(job_id=str(uuid4()), user_id=user_id, document_ids=document_ids)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get_job(self, *, job_id: str, user_id: int) -> _JobState | None:
        with self._lock:
            job = self._jobs.get(job_id)
        if not job or job.user_id != user_id:
            return None
        return job

    def to_response(self, job: _JobState) -> JobStatusResponse:
        total = max(len(job.document_ids), 1)
        progress = (job.processed_documents / total) * 100
        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            total_documents=len(job.document_ids),
            processed_documents=job.processed_documents,
            success_count=job.success_count,
            failure_count=job.failure_count,
            progress_percent=round(progress, 2),
            started_at=job.started_at,
            finished_at=job.finished_at,
            error=job.error,
        )

    def run_job(self, *, job_id: str, db) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.status = "running"

        try:
            doc_repo = DocumentRepository()
            metadata_service = MetadataService()

            for document_id in job.document_ids:
                try:
                    owned_doc = doc_repo.get_by_id_for_user(db, document_id, job.user_id)
                    if not owned_doc:
                        raise ValueError("Document not found or not owned by user")

                    if not owned_doc.extracted_text:
                        raise ValueError("Document has no extracted text")

                    if owned_doc.processing_status in {
                        DocumentStatus.UPLOADED,
                        DocumentStatus.FAILED,
                        DocumentStatus.COMPLETED,
                    }:
                        from app.services.document_status_service import DocumentStatusService

                        DocumentStatusService().update_status(
                            db,
                            owned_doc.id,
                            DocumentStatus.PROCESSING,
                            "Queued for batch metadata extraction",
                        )

                    metadata_service.process_and_extract(db, owned_doc, owned_doc.extracted_text)
                    job.success_count += 1
                except Exception:
                    job.failure_count += 1
                finally:
                    job.processed_documents += 1

            job.status = "completed" if job.failure_count == 0 else "failed"
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
        except Exception as exc:
            db.rollback()
            job.status = "failed"
            job.error = str(exc)
            job.finished_at = datetime.now(timezone.utc)
