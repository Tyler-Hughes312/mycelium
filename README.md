# Mycelium

Local-first context layer for AI-heavy developers — desktop console, VS Code side panel, and Core API stub.

## Structure

| Path | Role |
|---|---|
| `apps/desktop` | Vite + React desktop console |
| `apps/vscode` | VS Code side panel extension |
| `packages/ui` | Shared UI primitives (`@mycelium/ui`) |
| `services/core` | FastAPI Core stub |

## Desktop

```bash
# Terminal A — Core API
cd services/core
# from repo root venv:
../venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8787

# Terminal B — Desktop UI
cd apps/desktop
npm install
npm run dev
```

Open http://localhost:5173 — routes: `/` Library, `/index`, `/search`, `/vault`, `/settings`.

Desktop proxies `/api/*` → Core on `127.0.0.1:8787`. Library loads `GET /workspaces`; Search posts `POST /query`; shell polls `GET /health`.

## Core API

Hexagonal package at `services/core/src/mycelium/` (editable install).

```bash
# one-time
./venv/bin/pip install -e "services/core[dev]"

# run (localhost only)
cd services/core
../../venv/bin/uvicorn main:app --reload --host 127.0.0.1 --port 8787
```

On first start, Core creates `~/.mycelium/config.toml` (upload disabled by default), plus `data/` and `vault/`.

Endpoints: `GET /health`, `GET /workspaces`, `POST /query`.

## Implementation tracking

- Sprint status: `_bmad-output/implementation-artifacts/sprint-status.yaml`
- **Epic 1 (Local Core Skeleton): done** — Stories 1.1–1.3
- **Epic 2:** in progress — 2.1 + 2.2 **done**; next 2.3 symbol parsing

## VS Code extension

```bash
cd apps/vscode
npm install && npm run compile
```

Open `apps/vscode` and press **F5**. See `apps/vscode/README.md`.
