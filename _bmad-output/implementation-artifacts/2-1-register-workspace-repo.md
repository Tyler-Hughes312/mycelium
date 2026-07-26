# Story 2.1: Register Workspace Repo

Status: done

## Story

As a developer,
I want to register a local git repo path,
so that Mycelium knows what to index (FR-2).

## Acceptance Criteria

1. **Given** Core Service running  
   **When** I `POST /workspaces` with a valid git path  
   **Then** the workspace is persisted and listed via `GET /workspaces`

2. **Given** a non-git path  
   **When** I `POST /workspaces`  
   **Then** I receive a structured error (not a 500)

## Tasks / Subtasks

- [x] Implement `JsonFileWorkspaceRepo` behind `WorkspaceRepo` port
- [x] `POST /workspaces` + persist under `~/.mycelium/data/`
- [x] Replace mock `GET /workspaces` with persisted list
- [x] Wire Library "Add workspace" to Core
- [x] Tests for happy path + non-git error

## Dev Agent Record

### Completion Notes

- Persist at `{data_dir}/workspaces.json`
- Structured 400: `{ detail: { code, message } }` for not_git_repo / not_found / etc.
- Library shows empty state until a git path is registered
- Note: this workspace folder itself is not yet a git repo — register any local git path to dogfood

### File List

- `services/core/src/mycelium/adapters/store/workspace_repo.py`
- `services/core/src/mycelium/adapters/http/app.py`
- `services/core/tests/test_scaffold.py`
- `apps/desktop/src/api/client.ts`
- `apps/desktop/src/pages/LibraryPage.tsx`
