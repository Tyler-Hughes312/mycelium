# Story 2.2: Git history ingestion

Status: done

## Story

As a developer,
I want Commit Nodes created from git history,
so that past decisions are queryable (FR-5).

## Acceptance Criteria

1. **Given** a registered Workspace Repo  
   **When** I start Initial Index  
   **Then** Commit Nodes exist for up to the configured history depth (default 500)

2. **And** each Node stores hash, author, timestamp, message, changed paths

## Tasks

- [x] Git history adapter (`git log`)
- [x] Persist Commit Nodes (idempotent by hash, AD-7)
- [x] `POST /workspaces/{id}/index` + `GET .../commits` + status
- [x] Update workspace `commits` count / status
- [x] Wire Index console UI
- [x] Tests

## Dev Agent Record

### Completion Notes

- `read_commit_history` via git log; depth from `~/.mycelium/config.toml` `[index] history_depth`
- Nodes at `{data_dir}/workspaces/{id}/commits.json`
- Index console: register, Run Index, Commit Nodes list, activity log
- 8 pytest tests passing

### File List

- `services/core/src/mycelium/adapters/git/history.py`
- `services/core/src/mycelium/adapters/store/commit_store.py`
- `services/core/src/mycelium/core/domain/index_service.py`
- `services/core/src/mycelium/core/config.py`
- `services/core/src/mycelium/adapters/http/app.py`
- `apps/desktop/src/api/client.ts`
- `apps/desktop/src/pages/IndexPage.tsx`
