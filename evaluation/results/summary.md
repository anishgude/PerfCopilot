# Evaluation Summary

PerfCopilot currently demonstrates validation in three layers:

- backend unit/integration tests for metric computation, parsing, upload/history APIs, and persistence
- frontend lint/build validation for the Next.js dashboard
- manual end-to-end smoke tests against local benchmark uploads

Most recent local validation:

- `backend`: `python -m pytest` -> 7 tests passed
- `backend`: `ruff check` and `black --check` passed
- `frontend`: `npm run lint` passed
- `frontend`: `npm run build` passed

This repository does not claim formal benchmark-model accuracy metrics beyond the implemented regression calculations and local validation artifacts.
