# Story 2.3: Symbol parsing (Py/TS/JS/Go)

Status: done

## Story

As a developer,
I want Symbols extracted via structural parsing,
so that Context attaches to functions/classes, not only files (FR-6).

## Acceptance Criteria

1. Supported languages produce Symbol Nodes with path, name, start/end line — **done**
2. Unsupported files still create File Nodes without Symbols — **done**

## Approach

AD-8 cheap path: Python `ast`; TS/JS/Go regex. File set via `git ls-files`.

## Dev Agent Record

- Stores: `{data_dir}/workspaces/{id}/files.json`, `symbols.json`
- Stable IDs: `file:{path}`, `symbol:{path}:{name}:{start_line}`
- API: `GET /workspaces/{id}/symbols`
- Index console shows Symbol Nodes list
- 9 pytest tests passing
