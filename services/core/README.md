# Mycelium Core Service

Hexagonal Python package (`src/mycelium`) — local-first Core for Desktop / Editor / MCP.

## Layout

```text
src/mycelium/
  core/domain/     # business logic (later)
  core/ports/      # GraphStore, EmbeddingRuntime, WorkspaceRepo
  core/config.py   # ~/.mycelium/config.toml + data dirs
  adapters/http/   # FastAPI
  adapters/{git,embeddings,store}/  # stubs for later epics
  bridges/         # pointer only — apps live in apps/desktop, apps/vscode
```

## Install (editable)

From repo root (preferred):

```bash
./venv/bin/pip install -e services/core
```

Or from this directory:

```bash
../../venv/bin/pip install -e .
```

## Run (bind localhost — AD-2)

```bash
# from services/core
../../venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8787
```

Equivalent: `uvicorn mycelium.adapters.http.app:app --host 127.0.0.1 --port 8787`

On startup Core creates:

- `~/.mycelium/config.toml` (network upload disabled by default)
- `~/.mycelium/data/`
- `~/.mycelium/vault/`

## Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | version, bind, privacy flags, paths |
| GET | `/workspaces` | mock library rows |
| POST | `/query` | mock hybrid RAG |

## Tests

```bash
../../venv/bin/pip install -e ".[dev]"
../../venv/bin/pytest
```
