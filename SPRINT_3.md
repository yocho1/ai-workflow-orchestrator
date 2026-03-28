# SPRINT 3: Metadata Review, Batch Processing, and Export

## Overview

Sprint 3 extended the metadata pipeline from single-document extraction into an operational workflow with:

- manual metadata correction,
- confidence-driven review queueing,
- batch extraction with progress tracking,
- downloadable CSV/PDF exports,
- export filtering and UX polish.

This sprint focused on making extraction usable at scale and reviewable by humans.

## Scope Breakdown

### Sprint 3A: Manual Metadata Review and Correction

Implemented a complete review/edit flow for extracted metadata:

- Backend endpoint for manual updates:
  - `PATCH /api/v1/documents/{document_id}/metadata`
- Frontend review dialog for:
  - document type correction,
  - confidence correction,
  - raw JSON extracted-data edits,
  - validation feedback on malformed JSON / invalid confidence values.

### Sprint 3B: Confidence Threshold and Review Queue

Added confidence-based quality gates:

- low-confidence metadata is flagged with:
  - `needs_review=true`,
  - `review_reason` details.
- review queue endpoint:
  - `GET /api/v1/documents/metadata/review-queue`
- frontend Review Queue panel with pending count and quick "Review Now" actions.

### Sprint 3C: Batch Extraction and Job Progress

Added multi-document extraction orchestration:

- batch kickoff endpoints:
  - `POST /api/v1/documents/metadata/batch/extract-metadata` (canonical)
  - `POST /api/v1/documents/batch/extract-metadata` (legacy compatibility)
- job status endpoint:
  - `GET /api/v1/jobs/{job_id}`
- backend in-memory job tracker with:
  - total/processed/success/failure counters,
  - progress percent,
  - terminal status and error fields.
- frontend batch controls:
  - "Extract All" action,
  - polling progress bar,
  - failure/success status handling.

### Sprint 3D: Export Pipeline and Filter UX

Implemented export features for operations/reporting:

- CSV export endpoint:
  - `GET /api/v1/documents/metadata/export/csv`
- PDF export endpoint:
  - `GET /api/v1/documents/metadata/export/pdf`
- shared export filters (CSV + PDF):
  - `document_type`
  - `needs_review`
  - `updated_from`
  - `updated_to`
- frontend export actions:
  - Export CSV
  - Export PDF
- filter UX improvements:
  - persisted filter state (localStorage),
  - inline invalid date-range validation,
  - active filter chips,
  - removable chips,
  - clear-all filter chip,
  - filtered table view + filtered batch-target behavior.

## Notable Fixes During Sprint 3

- Route ambiguity fix for batch extraction (`path.document_id` parsing issue).
- Frontend/backend endpoint alignment on canonical batch path.
- Improved 422 validation detail surfacing in frontend error handling.
- Re-extraction stabilization in metadata transition/update flow.
- Better resilience when review queue loading fails (documents table remains usable).

## API Additions (Sprint 3)

- `GET /api/v1/documents/metadata/review-queue`
- `PATCH /api/v1/documents/{document_id}/metadata`
- `POST /api/v1/documents/metadata/batch/extract-metadata`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/documents/metadata/export/csv`
- `GET /api/v1/documents/metadata/export/pdf`

## Key Files Added/Updated

### Backend

- `backend/app/api/v1/routes/metadata.py`
- `backend/app/api/v1/routes/jobs.py`
- `backend/app/api/v1/router.py`
- `backend/app/schemas/jobs.py`
- `backend/app/services/batch_extraction_jobs.py`
- `backend/tests/test_metadata_api.py`
- `backend/requirements.txt` (added `reportlab` for PDF export)

### Frontend

- `frontend/src/pages/DocumentsPage.tsx`
- `frontend/src/services/metadata.ts`
- `frontend/src/services/jobs.ts`
- `frontend/src/services/http.ts`
- `frontend/src/types/api.ts`

## Validation Summary

Executed during Sprint 3 implementation and fixes:

- backend metadata API test suite passing
- frontend production build passing
- live endpoint checks for:
  - batch extraction route wiring,
  - export route availability,
  - auth-protected behavior.

## Representative Sprint 3 Commits

- `0a8d6f0` - manual metadata review flow (3A)
- `5eeb8a4` - confidence threshold review queue (3B)
- `ff909b1` - batch jobs + progress polling (3C)
- `a262813` - CSV export endpoint/UI (3D)
- `49897db` - PDF export endpoint/UI (3D)
- `9e706c0` - export filter support (3D)
- `61165da` - persisted filters + reset action (3D)
- `4f8414b` - inline date-range validation UX (3D)
- `1c30ae3` - removable active filter chips (3D)

## Outcome

Sprint 3 is complete: metadata extraction is now reviewable, scalable (batch), trackable (jobs), and exportable (CSV/PDF) with practical UI controls for real-world operations.
