# API Overview

Base URL: `http://localhost:8000`

## Endpoints

### `GET /health`

Simple health check.

### `POST /analyze`

Stateless benchmark analysis.

- input: benchmark payload JSON
- output:
  - raw model text
  - parsed diagnosis sections when available
  - computed slowdown and memory-growth metrics
  - fit metadata

### `POST /upload-benchmark`

Persisted benchmark analysis.

Supports:

- JSON request body
- multipart file upload with a `.json` benchmark file

Returns:

- `run_id`
- `status`
- computed metrics
- parsed diagnosis
- raw model output

### `GET /runs`

Returns recent analyses, newest first, with lightweight metadata.

### `GET /runs/{run_id}`

Returns a full persisted run:

- raw benchmark payload
- stored model output
- parsed diagnosis JSON
- computed metrics
- fit metadata
- status and error fields

### `DELETE /runs/{run_id}`

Deletes a persisted run.

## Auth

Auth is optional.

- set `ENABLE_API_KEY_AUTH=true`
- send `X-API-Key`

When disabled, local development is frictionless.
