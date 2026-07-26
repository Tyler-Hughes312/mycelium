# Story 2.5: Incremental file update hook

Status: done

## Story

As a developer,
I want changed files re-ingested automatically,
so that the Graph stays fresh (FR-4).

## Acceptance Criteria

1. Modify a tracked source file → File/Symbol Nodes upsert quickly — **done**
2. Node IDs remain stable (AD-7) — **done** (`symbol:path:name:start_line`)

## Delivered

- `POST /workspaces/{id}/hooks/file-changed` `{ "path": "..." }`
- `IndexService.reindex_file` path-scoped symbol replace
- `watchdog` watchers auto-start for registered workspaces (debounced)
- 11 pytest tests passing
