# AI Workflow Orchestrator

Production-ready monorepo foundation for an AI-powered Business Workflow Automation Platform.

## Sprint 1 Scope

- Monorepo setup with `backend`, `frontend`, and `infra`
- FastAPI base service with PostgreSQL connectivity check
- React + TypeScript dashboard shell with sidebar/header layout
- Docker Compose orchestration for `backend`, `frontend`, and `db`
- Environment-driven configuration and structured JSON logging

## Repository Structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |   `-- v1/
|   |   |       |-- routes/
|   |   |       |   `-- health.py
|   |   |       `-- router.py
|   |   |-- core/
|   |   |   |-- config.py
|   |   |   |-- db.py
|   |   |   |-- exceptions.py
|   |   |   |-- logging.py
|   |   |   `-- response.py
|   |   |-- models/
|   |   |-- pipelines/
|   |   |-- repositories/
|   |   |-- schemas/
|   |   |-- services/
|   |   `-- workers/
|   |-- Dockerfile
|   |-- requirements.txt
|   `-- .env.example
|-- frontend/
|   |-- src/
|   |   |-- components/
|   |   |   `-- layout/
|   |   |-- hooks/
|   |   |-- pages/
|   |   |-- services/
|   |   `-- state/
|   |-- Dockerfile
|   |-- package.json
|   `-- .env.example
|-- infra/
|   `-- docker-compose.yml
|-- .env.example
`-- README.md
```

## Prerequisites

- Docker Desktop (recommended for Sprint 1)
- Optional local runtime: Python 3.11+, Node.js 20+

## Quick Start (Docker)

1. From repository root, run:

   ```bash
   docker compose -f infra/docker-compose.yml up --build
   ```

2. Validate services:

- Backend health: `http://localhost:8000/api/v1/health`
- Frontend dashboard: `http://localhost:5173`

3. Stop services:

   ```bash
   docker compose -f infra/docker-compose.yml down
   ```

## Local Development (Without Docker)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

### One-Command Local Start/Stop (Windows PowerShell)

From repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-local.ps1
```

To stop local services by port:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop-local.ps1
```

## API Conventions (Implemented from Sprint 1)

- Versioned routes under `/api/v1`
- Standard response envelope:

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

- Global exception handling and validation response normalization
- Structured JSON logs for requests and errors

## Sprint Progress

- [x] Sprint 1 - Project Setup & Architecture
- [ ] Sprint 2 - Database & Core Models
- [ ] Sprint 3 - ETL Pipeline
- [ ] Sprint 4 - AI Integration (RAG + Classification)
- [ ] Sprint 5 - Frontend Dashboard Expansion
- [ ] Sprint 6 - Auth & User Logic
- [ ] Sprint 7 - QA & Evaluation
- [ ] Sprint 8 - Polish & Production
