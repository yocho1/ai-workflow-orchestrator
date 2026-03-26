# SPRINT 1: Document Lifecycle System

## Overview

Implemented a complete document status workflow with state machine validation, ensuring documents flow through a well-defined lifecycle: **uploaded → processing → classified → completed** (or fail at any stage with retry capability).

## Changes Made

### Backend

#### 1. **Document Status Enum** (`app/models/enums.py`)

- Created `DocumentStatus` enum with 5 states:
  - `uploaded`: Initial state after upload
  - `processing`: Currently being processed
  - `classified`: AI classification complete
  - `completed`: Ready for use
  - `failed`: Processing failed
- Defined state machine transitions as `VALID_STATUS_TRANSITIONS` dict

#### 2. **Model Updates** (`app/models/document.py`)

- Updated `processing_status` field to use `DocumentStatus` enum
- Maintains SQLAlchemy compatibility with string storage

#### 3. **Schema Updates** (`app/schemas/document.py`)

- Updated `DocumentBase` schema to use `DocumentStatus` enum
- Added new `DocumentStatusUpdate` request schema for status update endpoint
- Strict type validation via Pydantic

#### 4. **Status Service** (`app/services/document_status_service.py`)

- New `DocumentStatusService` class handling:
  - **State machine validation**: `validate_transition()` ensures only valid transitions
  - **Status updates**: `update_status()` atomically updates status + creates audit log
  - **Transition querying**: `get_valid_next_statuses()` returns allowed next states
- Comprehensive error messages for invalid transitions
- Integration with processing logs for full audit trail

#### 5. **API Endpoint** (`app/api/v1/routes/documents.py`)

- New **POST** `/documents/{document_id}/status` endpoint
  - Request body: `DocumentStatusUpdate` (status + optional message)
  - Response: Updated `DocumentRead` document
  - Error handling: 404 (not found), 422 (invalid transition), 403 (unauthorized)
  - Full ownership validation
  - Detailed error messages for debugging

### Frontend

#### 1. **StatusBadge Component** (`frontend/src/components/StatusBadge.tsx`)

- Reusable React component displaying document status with:
  - **Color coding**:
    - `default` (gray) for uploaded
    - `info` (blue) for processing
    - `success` (green) for classified & completed
    - `error` (red) for failed
  - **Emoji labels**: Visual indicators for quick scanning
  - **MUI Chip**: Material-UI consistent styling

#### 2. **DocumentsPage Updates** (`frontend/src/pages/DocumentsPage.tsx`)

- Replaced plain text status with new `StatusBadge` component
- Enhanced visual clarity of document status
- Ready for future status update UI interactions

### Tests

#### 1. **Unit Tests** (`tests/test_document_status_service.py`)

- **Transition validation** (13 tests):
  - All valid transitions documented and tested
  - Invalid transitions properly rejected
  - Same-status validation
  - Non-existent document handling
- **Audit logging**: Verifies logs created on every status change
- **Custom messages**: Confirms custom messages stored in logs
- **Lifecycle tests**:
  - Happy path: complete workflow
  - Failure + retry: realistic scenario
- **Utility tests**: `get_valid_next_statuses()` correctness

#### 2. **Integration Tests** (`tests/test_document_status_api.py`)

- **API endpoint tests** (11 tests):
  - Valid transitions via HTTP
  - Custom message support
  - Invalid transition rejection (422 error)
  - Document not found (422 error)
  - Authorization checks (403 for cross-user, 401 for no auth)
- **Lifecycle via API**: Full end-to-end flow
- **Reprocessing & retry**: Realistic workflows
- **Error handling**: Invalid enum values rejected properly

#### Coverage:

- ✅ All happy paths
- ✅ All error cases
- ✅ State machine correctness
- ✅ Authorization & access control
- ✅ Audit logging

## Architecture

### State Machine Diagram

```
┌─────────────────────────────────────────────┐
│                   UPLOADED                  │
│         (initial state after upload)        │
└──────────────┬──────────────────────────────┘
               │
         ┌─────┴─────┐
         ▼           ▼
      PROCESSING   FAILED
         │           │
         │ ┌─────────┘
         ▼ ▼
    CLASSIFIED (can retry)
         │
         ▼
      COMPLETED ─────┐
                    │
                    └─ (reprocess)

Invalid transitions are rejected with descriptive error messages.
Failed documents can be retried by transitioning back to processing.
Completed documents can be reprocessed if needed.
```

### Design Principles

1. **Type Safety**: Enum-based states prevent string typos
2. **Immutability**: State transitions are unidirectional (except retry paths)
3. **Auditability**: Every status change logged with timestamp & reason
4. **Atomicity**: Status + log created together
5. **Composability**: Service can be injected into other services

## How to Run

### 1. Run Backend

```bash
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Run Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at `http://localhost:5173`

### 3. Run Tests

#### Unit + Integration Tests:

```bash
cd backend
..\.venv\Scripts\python.exe -m pytest tests/test_document_status_service.py -v
..\.venv\Scripts\python.exe -m pytest tests/test_document_status_api.py -v
```

#### Run all tests:

```bash
cd backend
..\.venv\Scripts\python.exe -m pytest tests/ -v
```

#### Run with coverage:

```bash
cd backend
..\.venv\Scripts\python.exe -m pytest tests/ --cov=app --cov-report=html
```

## Testing the Feature

### Manual Testing via Frontend

1. **Login**: Navigate to http://localhost:5173
2. **Upload document**: Use upload button
3. **View status**: Document appears in table with status badge
4. **Current status**: Shows in colored chip (📤 Uploaded)

### Manual Testing via API

#### Using cURL:

```bash
# 1. Create document
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test.txt",
    "content_type": "text/plain",
    "storage_path": "/uploads/test.txt",
    "extracted_text": "Test content"
  }'

# Response includes document with status: "uploaded"
# Save the document ID

# 2. Update status: uploaded → processing
curl -X POST http://localhost:8000/api/v1/documents/1/status \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status": "processing"}'

# 3. Update status: processing → classified
curl -X POST http://localhost:8000/api/v1/documents/1/status \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status": "classified"}'

# 4. Update status: classified → completed
curl -X POST http://localhost:8000/api/v1/documents/1/status \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'

# 5. Try invalid transition (should fail with 422):
curl -X POST http://localhost:8000/api/v1/documents/1/status \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status": "processing"}'
  # Error: Cannot transition from 'completed' to 'processing'
  # (unless via special endpoint for reprocessing)
```

## Git Commit Message

```
feat(lifecycle): implement document status lifecycle with state machine

- Add DocumentStatus enum with 5 states (uploaded, processing, classified, completed, failed)
- Implement state machine validation with VALID_STATUS_TRANSITIONS
- Create DocumentStatusService for atomic status updates with audit logging
- Add POST /documents/{id}/status endpoint with transition validation
- Update models & schemas to use DocumentStatus enum
- Create StatusBadge React component with color coding & emoji labels
- Add 24 comprehensive tests (13 unit + 11 integration)
- Full authorization & ownership checks
- Support for custom messages on status changes
- Retry capability: failed → processing, completed → processing
- Complete audit trail via ProcessingLog

Closes: #1 (assuming this is the first feature)
```

## Files Modified/Created

### Created:

- ✅ `backend/app/models/enums.py` - Status enum + state machine
- ✅ `backend/app/services/document_status_service.py` - Status service
- ✅ `backend/tests/test_document_status_service.py` - Unit tests
- ✅ `backend/tests/test_document_status_api.py` - Integration tests
- ✅ `frontend/src/components/StatusBadge.tsx` - Status badge component

### Modified:

- ✅ `backend/app/models/document.py` - Use DocumentStatus enum
- ✅ `backend/app/schemas/document.py` - Use DocumentStatus enum + add DocumentStatusUpdate
- ✅ `backend/app/api/v1/routes/documents.py` - Add status update endpoint
- ✅ `frontend/src/pages/DocumentsPage.tsx` - Use StatusBadge component

## Verification Checklist

- ✅ Status transitions validated (state machine)
- ✅ Invalid transitions rejected with clear error messages
- ✅ API endpoint responds with correct HTTP codes
- ✅ Authorization checks (ownership, authentication)
- ✅ Audit logs created for every status change
- ✅ Frontend displays status badges with correct colors
- ✅ All tests passing
- ✅ No breaking changes to existing code
- ✅ Type-safe enum usage throughout
- ✅ Production-ready error handling

## Next Steps

SPRINT 2 will build on this foundation to add **AI-Driven Actions**:

- Extract structured metadata based on document type
- Automatically trigger processing based on status transitions
- Store extracted data (amount, due date, key clauses, etc.)
