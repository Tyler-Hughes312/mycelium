# Story 1.2: Localhost HTTP API health

Status: done

## Story

As a developer,
I want a FastAPI health endpoint on localhost,
so that bridges can detect the Core Service.

## Acceptance Criteria

1. **Given** Core Service started  
   **When** I `GET /health`  
   **Then** I receive 200 with service version  
   **And** the bind address defaults to `127.0.0.1` (AD-2)

## Completion Notes

- `/health` returns `version`, `bind.host/port`, privacy flags, and local paths
- Default uvicorn bind documented as `--host 127.0.0.1`
- Covered by `tests/test_scaffold.py::test_health_includes_version`
