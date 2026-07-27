# Mycelium

[![CI](https://github.com/Tyler-Hughes312/mycelium/actions/workflows/ci.yml/badge.svg)](https://github.com/Tyler-Hughes312/mycelium/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.2-0ea5e9.svg)](CHANGELOG.md)
[![Site](https://img.shields.io/badge/site-getmycelium.vercel.app-black.svg)](https://getmycelium.vercel.app)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-3776AB.svg)](services/core/pyproject.toml)
[![Local-first](https://img.shields.io/badge/privacy-local--first-22c55e.svg)](docs/DEPLOY.md)

**Local-first context layer for AI-heavy developers.**

Stop burning tokens re-reading and re-searching your codebase every session. Mycelium **indexes your repos locally** (symbols, files, commits) and returns a **precise context packet** to Cursor / Claude via MCP — so agents spend context on the answer, not the haystack.

This is **not** a chat journal or “agent memory vault.” Those tools optimize for remembering conversations. Mycelium optimizes for **efficient retrieval from your project structure** — a stronger, more demoable pitch (tokens saved vs paste-the-file / re-grep).

```text
  Cursor / Claude ──MCP──► mycelium-mcp ──► Core :8787
  Desktop (Vite)  ──HTTP──────────────────► Core :8787
  VS Code panel   ──HTTP──────────────────► Core :8787
                         │
                         ├── ~/.mycelium/data (indexes)  ← primary
                         └── ~/.mycelium/vault           ← optional decisions/ADRs
```

## Why Mycelium

| | |
|---|---|
| **Token efficiency (headline)** | Tight focus/search packets vs dumping files or grepping every session |
| **Codebase-first index** | Project structure, symbols, commits — not conversation transcripts |
| **Measurable impact** | Desktop **Impact** estimates tokens saved locally (served vs baseline dump) |
| **Private by default** | Localhost only; upload / remote LLM are opt-in |
| **Three surfaces** | Desktop console · editor side panel · agent MCP tools |

**vs agent memory / “context vault” products:** they remember what you *said*. Mycelium retrieves what your *code* already contains. Thinking Vault notes are optional secondary context (decisions, ADRs) — not the core product.

## Download Desktop

Install a packaged app (Core is bundled — no Python/Node required):

- **Latest release:** https://github.com/Tyler-Hughes312/mycelium/releases/tag/v0.1.2-desktop  
- **All releases:** https://github.com/Tyler-Hughes312/mycelium/releases  
- **Install notes (Gatekeeper / SmartScreen):** [docs/DESKTOP-INSTALL.md](docs/DESKTOP-INSTALL.md)
- **Marketing site:** https://getmycelium.vercel.app  

Build locally:

```bash
./scripts/package-desktop.sh   # → .dmg under apps/desktop/src-tauri/target/release/bundle/
```

## Use with Cursor / Claude (MCP)

Mycelium MCP is how agents get indexed context packets. Core must be running on `127.0.0.1:8787` (Desktop app **or** `./scripts/dev.sh` / `mycelium serve`).

### 1. Install the MCP bridge

```bash
git clone https://github.com/Tyler-Hughes312/mycelium.git
cd mycelium
./scripts/install.sh          # creates venv + mycelium-mcp
```

Or point Cursor at the absolute binary: `…/mycelium/venv/bin/mycelium-mcp`.

### 2. Add MCP config (Cursor)

Copy [`templates/cursor/mcp.json.example`](templates/cursor/mcp.json.example) → `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "mycelium": {
      "command": "/ABSOLUTE/PATH/TO/mycelium/venv/bin/mycelium-mcp",
      "args": [],
      "env": { "MYCELIUM_CORE_URL": "http://127.0.0.1:8787" }
    }
  }
}
```

Optional agent rule: copy [`templates/cursor/mycelium-mcp.mdc`](templates/cursor/mycelium-mcp.mdc) → `.cursor/rules/`.

### 3. Index once, then ask

1. Open Desktop (or web UI) → **Library** → add your repo → **Index**
2. Reload Cursor MCP
3. Ask the agent to use Mycelium (`mycelium_search` / `mycelium_focus`) instead of grepping the whole tree

Full write/read policy: [docs/AGENT-SECOND-BRAIN.md](docs/AGENT-SECOND-BRAIN.md) · ops: [docs/DEPLOY.md](docs/DEPLOY.md#mcp-path-based)

## Develop from source (≈15 minutes)

**Needs:** macOS/Linux · Python 3.12+ · Node.js · git

```bash
git clone https://github.com/Tyler-Hughes312/mycelium.git
cd mycelium
./scripts/install.sh
./scripts/dev.sh          # Core :8787 + Desktop :5173
```

Open **http://localhost:5173** → Library → add `fixtures/dogfood-rate-limits` → Index → Search: `how did we handle rate limits`.

| Surface | Command |
|---|---|
| Production Core | `./scripts/run-core.sh` → `mycelium serve` |
| Desktop preview | `./scripts/run-desktop.sh` → `:4173` |
| Native Desktop | `./scripts/package-desktop.sh` or `cd apps/desktop && npm run tauri:dev` |
| VS Code / Cursor | `cd apps/vscode && npm run package` → install `.vsix` |
| Agents (MCP) | `mycelium-mcp` — [second brain guide](docs/AGENT-SECOND-BRAIN.md) |

### Upgrade / uninstall

```bash
git pull && ./scripts/install.sh     # keeps ~/.mycelium data
rm -rf venv                          # tooling only
rm -rf ~/.mycelium                   # optional: wipe vault + indexes
```

## Repository layout

| Path | Role |
|---|---|
| [`apps/desktop`](apps/desktop) | Vite + React console (Library, Index, Search, Vault, Settings) |
| [`apps/web`](apps/web) | Marketing site (Vercel) — see [apps/web/README.md](apps/web/README.md) |
| [`apps/vscode`](apps/vscode) | Side panel Context + New Note (`.vsix`) |
| [`packages/ui`](packages/ui) | Shared chips / result rows |
| [`services/core`](services/core) | FastAPI Core + MCP bridge (`mycelium`, `mycelium-mcp`) |
| [`fixtures/dogfood-rate-limits`](fixtures/dogfood-rate-limits) | Demo git repo for first Context |
| [`docs/`](docs) | Deploy, demo, dogfood, agent docs |

## Docs

- [Positioning](docs/POSITIONING.md) — token efficiency vs agent-memory products
- [Deploy / ops](docs/DEPLOY.md) — install, MCP, release gate
- [Connect GitHub](docs/GITHUB.md) — import repos for cross-repo search
- [Agent second brain](docs/AGENT-SECOND-BRAIN.md) — MCP read/write loop
- [Demo script](docs/DEMO.md) · [Dogfood checklist](docs/DOGFOOD-CHECKLIST.md)
- [Changelog](CHANGELOG.md) · [License (MIT)](LICENSE)

## Troubleshooting

| Symptom | Fix |
|---|---|
| Core offline in Desktop | `./scripts/run-core.sh` · check `~/.mycelium/logs/` |
| Blank UI / CORS | Core on `127.0.0.1:8787`; open `:5173` or `:4173` |
| `mycelium-mcp` missing | Use `…/venv/bin/mycelium-mcp` in MCP config |
| Empty search | Index the workspace; first embedding download can take a minute |
| Extension offline | Setting `mycelium.coreUrl` → Retry Connection |

## Maintainer

```bash
./scripts/release-check.sh           # CI-equivalent locally
cd services/core && ../../venv/bin/pytest -q
```

Default embedding: `sentence-transformers/all-MiniLM-L6-v2` (cached under `~/.mycelium/models`).

---

<p align="center">
  <sub>Built for developers who want indexed code context — without uploading the repo or re-burning tokens every chat.</sub>
</p>
