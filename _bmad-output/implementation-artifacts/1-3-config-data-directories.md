# Story 1.3: Config + data directories

Status: done

## Story

As an AI-heavy developer,
I want Mycelium config and data under well-known local paths,
so that my repos are not uploaded and state survives restart.

## Acceptance Criteria

1. **Given** first run  
   **When** Core Service starts  
   **Then** it creates `~/.mycelium/config.toml` and a local data dir  
   **And** config documents that network for code upload is disabled by default (FR-19)

## Completion Notes

- `mycelium.core.config.ensure_local_layout()` runs on FastAPI lifespan startup
- Creates `~/.mycelium/config.toml`, `data/`, `vault/`
- Defaults: `allow_code_upload = false`, `allow_remote_llm = false`, `host = "127.0.0.1"`
- Covered by `tests/test_scaffold.py::test_ensure_local_layout`
