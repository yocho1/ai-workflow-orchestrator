# SPRINT 8: Polish and Production

## Objective

Sprint 8 focuses on production hardening: reliable automation, release confidence, and operational readiness.

## Checklist

- [x] Add GitHub Actions CI workflow for push and pull request validation
- [x] Automate Sprint 7 smoke test in CI against a live backend process
- [ ] Add deployment runbook with rollback procedure
- [ ] Add baseline monitoring and alerting checklist
- [ ] Add production environment variable matrix
- [ ] Add incident response checklist

## Implemented in This Kickoff

### CI Workflow

File: `.github/workflows/ci.yml`

Current pipeline coverage:

- backend unit/integration tests (`backend/tests`)
- frontend production build (`npm run build`)
- Sprint 7 smoke test (`sprint7_qa_smoke_test.py`) with:
  - SQLite-backed backend startup,
  - migration application (`alembic upgrade head`),
  - health endpoint readiness wait,
  - backend log artifact upload.

## Next Deliverables

1. Add release runbook and rollback command examples.
2. Add minimal observability baseline (health probes, log retention guidance, and on-call checks).
3. Add production deployment verification checklist.
