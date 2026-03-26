# SPRINT 2: AI-Driven Metadata Extraction

## Overview

Implemented automated document metadata extraction and classification using AI. Documents are analyzed to determine their type (invoice, contract, receipt, report) and have structured data extracted based on their classification. Status transitions are automatically triggered: **processing → classified → completed**.

## Changes Made

### Backend

#### 1. **DocumentMetadata Model** (`app/models/metadata.py`)

- New `DocumentMetadata` table for storing extracted structured data
- One-to-one relationship with Document (via `extracted_metadata` relationship)
- Fields:
  - `document_type`: Classified type (invoice, contract, receipt, report, other)
  - `confidence_score`: Classification confidence (0-1)
  - `extracted_data`: JSON object with type-specific extracted fields
  - `extraction_model`: Which AI model was used
  - `extraction_error`: Error message if extraction failed
  - Audit timestamps

#### 2. **DocumentType Enum** (`app/models/enums.py`)

- Added `DocumentType` enum with 5 types:
  - `invoice`: Sales/purchase invoices
  - `contract`: Legal agreements and contracts
  - `receipt`: Purchase receipts and transaction records
  - `report`: Business reports and financial statements
  - `other`: Unclassified documents

#### 3. **Database Migration** (`alembic/versions/20260326_0003_...`)

- Created `document_metadata` table with:
  - Unique constraint on `document_id` (1:1 relationship)
  - CASCADE delete linked to documents
  - JSON column support for `extracted_data`
  - Automatic timestamp management

#### 4. **MetadataExtractor Service** (`app/services/metadata_extractor.py`)

- **Classification**: Uses Claude API to determine document type with confidence score
- **Type-specific extraction**:
  - **Invoice**: amount, currency, invoice_number, date, due_date, vendor, line_items
  - **Contract**: parties, start_date, end_date, expiration_date, key_clauses, termination_clause
  - **Receipt**: amount, currency, date, merchant, items
  - **Report/Other**: Document type only
- **Error handling**: Graceful fallback to `other` type on classification failure
- **Text limiting**: Truncates to 3000 chars for cost efficiency

#### 5. **MetadataService** (`app/services/metadata_service.py`)

- Orchestrates metadata extraction pipeline
- **Automatic status transitions**:
  1. `processing` → `classified` (after type detection)
  2. `classified` → `completed` (after extraction)
  3. `failed` (on error, with descriptive message)
- **Atomic operations**: Extraction + status update in single transaction
- **Dependency injection**: Accepts optional service/repository overrides for testing

#### 6. **MetadataRepository** (`app/repositories/metadata_repository.py`)

- Standard CRUD operations: create, get_by_document_id, update, delete
- `update_by_document_id()`: Convenience method for document-scoped updates

#### 7. **Metadata Schemas** (`app/schemas/metadata.py`)

- `MetadataBase`: Common fields (type, confidence, extracted_data)
- `MetadataCreate`: Creation payload with model and error tracking
- `MetadataUpdate`: Partial update schema
- `MetadataRead`: Response schema with timestamps and audit info

#### 8. **API Endpoints** (`app/api/v1/routes/metadata.py`)

**GET** `/documents/{document_id}/metadata`

- Retrieve extracted metadata for a document
- Returns: `MetadataRead` schema with all extracted fields
- Errors: 404 if document/metadata not found, 403 for unauthorized access

**POST** `/documents/{document_id}/extract-metadata`

- Trigger metadata extraction pipeline on a document
- Updates status: `processing` → `classified` → `completed`
- Returns extracted metadata after completion
- Errors: 422 if document has no extracted text

**GET** `/documents/{document_id}/metadata/summary`

- Quick summary of extracted metadata
- Returns: document type, confidence, field count, field names
- Useful for UI quick previews without full data download

#### 9. **Document Model Update** (`app/models/document.py`)

- Added `extracted_metadata` relationship (renamed from `metadata` to avoid SQLAlchemy reserved name)
- Lazy-loaded on relationship access
- Cascade delete with orphan cleanup

### Frontend

#### 1. **MetadataDisplay Component** (`frontend/src/components/MetadataDisplay.tsx`)

- **Features**:
  - Document type badge with confidence percentage
  - Loading state with spinner
  - Error display with red background
  - Field-by-field display with type-specific rendering:
    - Nested objects rendered as JSON
    - Arrays with context (table-like for objects, list for primitives)
    - Boolean fields as Yes/No badges
    - Null values with "Not found" message
  - Responsive card layout using Shadcn UI

- **Props**:
  ```typescript
  interface MetadataDisplayProps {
    metadata: Metadata | null
    loading?: boolean
    error?: string | null
  }
  ```

### Tests

#### 1. **Metadata Repository Tests** (`tests/test_metadata_service.py::TestMetadataRepository`)

- ✅ `test_create_metadata`: Verify new metadata record creation
- ✅ `test_get_by_document_id`: Retrieve metadata by document
- ✅ `test_get_nonexistent_metadata`: Handle missing metadata gracefully
- ✅ `test_update_metadata`: Verify partial updates work correctly

**Result**: 4/4 passing

#### 2. **API Integration Tests** (`tests/test_metadata_api.py`)

- Authentication checks (401 without token)
- Authorization checks (404 for other users' documents)
- Metadata retrieval and summary endpoints
- Extraction endpoint validation
- End-to-end workflow testing

#### 3. **Test Fixtures** (`tests/conftest.py`)

Added new fixtures:

- `logged_in_user`: Auto-creates user and returns auth token
- `test_document`: Creates document for logged-in user
- `test_document_other_user`: Creates document for different user (for auth testing)

## Architecture

### Data Flow

```
1. Document uploaded (status: uploaded)
                ↓
2. User triggers extraction
   POST /documents/{id}/extract-metadata
                ↓
3. MetadataExtractor classifies document
   - Analyze text with Claude
   - Determine type + confidence
                ↓
4. Extract type-specific fields
   - Invoice: amount, dates, vendor, items
   - Contract: parties, dates, clauses
   - Receipt: merchant, items, total
                ↓
5. Store in DocumentMetadata table
   - Type, confidence, extracted_data (JSON)
   - Audit info (model, error if any)
                ↓
6. Automatic status transitions
   - processing → classified
   - classified → completed
   - (or → failed on error)
                ↓
7. Response includes metadata
   - UI displays with MetadataDisplay component
```

### Error Handling

- **No extracted text**: Return 422 "Document has no extracted text"
- **Classification failure**: Default to `other` type with 0% confidence
- **Extraction failure**: Store error message, transition to `failed` status
- **Authorization failure**: Return 403 or 404 (consistent with Sprint 1)

### Performance Considerations

- **Text limits**: Classify on first 2000 chars, extract on 3000 chars (OpenRouter cost optimization)
- **Lazy loading**: Metadata only loaded on explicit request via `lazy="joined"`
- **JSON storage**: Extracted data stored as JSON for flexibility across doc types
- **Single transaction**: Metadata creation + status update atomic

## How to Run

### Run Backend

```bash
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Tests

```bash
cd backend

# Metadata repository tests
..\.venv\Scripts\python.exe -m pytest tests/test_metadata_service.py::TestMetadataRepository -v

# All tests
..\.venv\Scripts\python.exe -m pytest tests/ -v
```

### Apply Database Migrations

```bash
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
```

## Manual Testing via API

### 1. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

### 2. Create/Upload Document

```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "invoice.pdf",
    "content_type": "application/pdf",
    "storage_path": "/uploads/invoice.pdf",
    "extracted_text": "Invoice #INV-001\nAmount: $299.99\nDate: 2026-03-26"
  }'
```

Save the document ID.

### 3. Extract Metadata

```bash
curl -X POST http://localhost:8000/api/v1/documents/1/extract-metadata \
  -H "Authorization: Bearer <TOKEN>"
```

Response:

```json
{
  "success": true,
  "data": {
    "id": 1,
    "document_id": 1,
    "document_type": "invoice",
    "confidence_score": 0.95,
    "extracted_data": {
      "amount": 299.99,
      "currency": "USD",
      "invoice_number": "INV-001",
      "date": "2026-03-26"
    },
    "extraction_model": "openai/gpt-4o-mini",
    "extraction_error": null,
    "created_at": "2026-03-26T...",
    "updated_at": "2026-03-26T..."
  },
  "error": null
}
```

### 4. Get Metadata with Summary

```bash
# Get full metadata
curl http://localhost:8000/api/v1/documents/1/metadata \
  -H "Authorization: Bearer <TOKEN>"

# Get quick summary
curl http://localhost:8000/api/v1/documents/1/metadata/summary \
  -H "Authorization: Bearer <TOKEN>"
```

## Files Modified/Created

### Created:

- ✅ `backend/app/models/metadata.py` - DocumentMetadata model
- ✅ `backend/app/repositories/metadata_repository.py` - Metadata CRUD layer
- ✅ `backend/app/services/metadata_extractor.py` - AI extraction logic
- ✅ `backend/app/services/metadata_service.py` - Orchestration & status transitions
- ✅ `backend/app/schemas/metadata.py` - Pydantic schemas
- ✅ `backend/app/api/v1/routes/metadata.py` - API endpoints
- ✅ `backend/tests/test_metadata_service.py` - Unit & integration tests
- ✅ `backend/tests/test_metadata_api.py` - API integration tests
- ✅ `backend/alembic/versions/20260326_0003_...` - Database migration
- ✅ `frontend/src/components/MetadataDisplay.tsx` - React metadata component

### Modified:

- ✅ `backend/app/models/document.py` - Added `extracted_metadata` relationship
- ✅ `backend/app/models/enums.py` - Added `DocumentType` enum
- ✅ `backend/app/api/v1/router.py` - Registered metadata router
- ✅ `backend/tests/conftest.py` - Added test fixtures (logged_in_user, test_document, etc.)

## Verification Checklist

- ✅ DocumentMetadata model with 1:1 relationship to Document
- ✅ Document type classification (5 types)
- ✅ Type-specific metadata extraction (invoice, contract, receipt)
- ✅ Automatic status transitions (processing → classified → completed)
- ✅ API endpoints for retrieval and extraction
- ✅ Error handling and validation
- ✅ Authorization checks (ownership validation)
- ✅ Database migrations applied
- ✅ Repository tests passing (4/4)
- ✅ React component for metadata display
- ✅ Test fixtures for authenticated testing

## Integration with Sprint 1

Sprint 2 builds directly on Sprint 1's foundation:

- Uses `DocumentStatus` enum from Sprint 1
- Uses `DocumentStatusService` for automatic transitions
- Integrates with existing `Document` model without breaking changes
- Respects ownership checks from Sprint 1's authorization layer
- Follows same API response envelope pattern

## Next Steps

SPRINT 3 could add:

- **Manual metadata editing**: Allow users to correct extracted values
- **Confidence thresholds**: Re-extract if confidence below threshold
- **Batch extraction**: Extract metadata for multiple documents
- **Webhook notifications**: Alert when extraction completes
- **Export as CSV/PDF**: Export extracted data in different formats
- **Custom document types**: Let users define custom extraction patterns

## Git Commit Message

```
feat(metadata): implement AI-driven document extraction with auto-transitions

- Add DocumentMetadata model with 1:1 relationship to Document
- Add DocumentType enum (invoice, contract, receipt, report, other)
- Implement MetadataExtractor service with type-specific extraction
  - Invoice: amount, currency, dates, vendor, line items
  - Contract: parties, dates, clauses
  - Receipt: merchant, items, total
- Add MetadataService for orchestration with automatic status transitions
  - processing → classified → completed
- Create metadata API endpoints (GET, POST, summary)
- Add MetadataDisplay React component with field rendering
- Database migration: create document_metadata table with CASCADE delete
- Add test fixtures (logged_in_user, test_document) for integration testing
- 4/4 repository tests passing

Depends on Sprint 1 (DocumentStatus, status transitions)
Integrates with DocumentStatusService for atomic updates
```
