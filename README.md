# Mycelium

<p align="center">
  <img src="apps/desktop/public/mycelium-logo.svg" alt="Mycelium" width="96" />
</p>

<p align="center">
  <strong>Local-first codebase context for AI coding</strong><br />
  Index once · serve tight MCP packets · stop burning tokens re-grepping
</p>

<p align="center">
  <a href="https://github.com/Tyler-Hughes312/mycelium/stargazers">⭐ Star this repo</a>
  ·
  <a href="https://getmycelium.vercel.app">Website</a>
  ·
  <a href="https://github.com/Tyler-Hughes312/mycelium/releases/tag/v0.1.3-desktop">Download Desktop</a>
  ·
  <a href="docs/marketing/">Marketing / launch</a>
</p>

[![CI](https://github.com/Tyler-Hughes312/mycelium/actions/workflows/ci.yml/badge.svg)](https://github.com/Tyler-Hughes312/mycelium/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.3-0ea5e9.svg)](CHANGELOG.md)
[![Site](https://img.shields.io/badge/site-getmycelium.vercel.app-black.svg)](https://getmycelium.vercel.app)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-3776AB.svg)](services/core/pyproject.toml)
[![Local-first](https://img.shields.io/badge/privacy-local--first-22c55e.svg)](docs/DEPLOY.md)
[![GitHub stars](https://img.shields.io/github/stars/Tyler-Hughes312/mycelium?style=social)](https://github.com/Tyler-Hughes312/mycelium/stargazers)

Stop burning tokens re-reading and re-searching your codebase every session. Mycelium **indexes your repos locally** (symbols, files, commits) and returns a **precise context packet** to Cursor / Claude via MCP — so agents spend context on the answer, not the haystack.

This is **not** a chat journal or “agent memory vault.” Those tools optimize for remembering conversations. Mycelium optimizes for **efficient retrieval from your project structure** — a stronger, more demoable pitch (tokens saved vs paste-the-file / re-grep).

**Agent loop:** `session_start` → **`reuse_check`** (plan/build) → task tools (`change_context` / `debug_context`) → cite the one-line **`receipt=`** instead of re-dumping the repo. Open a git repo in Cursor with Core running and **`workspaceOpen` auto-indexes**. Desktop **Impact** shows **grounded %** (recalls with a receipt vs without).

**Easy setup:** [Desktop + vault + agents](docs/GETTING-STARTED.md) — launch Desktop (vault scaffolds at `~/.mycelium/vault`), run `./scripts/install.sh` once to wire Cursor / VS Code / Codex / Claude / Windsurf.

**30-second try:** Desktop (or `./scripts/dev.sh`) → Library → add `fixtures/dogfood-rate-limits` → Index → ask your agent via MCP: *how did we handle rate limits?*

```text
  Cursor / Claude ──MCP──► mycelium-mcp ──► Core :8787
  Desktop (Vite)  ──HTTP──────────────────► Core :8787
  VS Code panel   ──HTTP──────────────────► Core :8787
                         │
                         ├── ~/.mycelium/data (indexes + receipts)  ← primary
                         └── ~/.mycelium/vault                      ← optional decisions/ADRs
```

## Why Mycelium

| | |
|---|---|
| **Token efficiency (headline)** | Tight focus/search packets vs dumping files or grepping every session |
| **Open → index** | Cursor `workspaceOpen` hook registers the git repo and starts indexing when Core is up |
| **Prior-art reuse** | `mycelium_reuse_check` — search all indexed repos; ask adapt vs build new before plan/build |
| **Session bootstrap** | `mycelium_session_start` / `preflight` — auto-register repo, optional index, compact brain + open-file focus |
| **Task-shaped tools** | `mycelium_change_context` / `mycelium_debug_context` — ranked hits for implement vs fix, not raw search lists |
| **Context receipts** | One-line `receipt=` attestation (paths/ids only) — cite it; `verify_receipt` checks staleness without re-dumping |
| **Measurable impact** | Desktop **Impact**: tokens/$ saved **and** grounded % (receipt-backed recalls) |
| **Private by default** | Localhost only; upload / remote LLM are opt-in |
| **Three surfaces** | Desktop console · editor side panel · agent MCP tools |

**vs agent memory / “context vault” products:** they remember what you *said*. Mycelium retrieves what your *code* already contains. Thinking Vault notes are optional secondary context (decisions, ADRs) — not the core product.

## Download Desktop

Install a packaged app (Core is bundled — no Python/Node required):

- **Latest release:** https://github.com/Tyler-Hughes312/mycelium/releases/tag/v0.1.3-desktop  
- **All releases:** https://github.com/Tyler-Hughes312/mycelium/releases  
- **Install notes (Gatekeeper / SmartScreen):** [docs/DESKTOP-INSTALL.md](docs/DESKTOP-INSTALL.md)
- **Then vault + agents:** [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md)
- **Marketing site:** https://getmycelium.vercel.app  

Build locally:

```bash
./scripts/package-desktop.sh   # → .dmg under apps/desktop/src-tauri/target/release/bundle/
```

## Use with Cursor / Claude (MCP)

Step-by-step (Desktop → Thinking Vault → agents): **[docs/GETTING-STARTED.md](docs/GETTING-STARTED.md)**.

Mycelium MCP is how agents get indexed context packets **and** vault tools. Core must be running on `127.0.0.1:8787` (Desktop app **or** `./scripts/dev.sh` / `mycelium serve`). First Core start scaffolds `~/.mycelium/vault/` automatically.

### 1. Install the MCP bridge

```bash
git clone https://github.com/Tyler-Hughes312/mycelium.git
cd mycelium
./scripts/install.sh          # creates venv + mycelium-mcp + wires agents
```

Or point Cursor at the absolute binary: `…/mycelium/venv/bin/mycelium-mcp`.

### 2. Wire MCP into your coding agents

`./scripts/install.sh` installs Mycelium into **Cursor, VS Code/Copilot, Codex, Windsurf, and Claude Desktop** (when present), plus a Cursor `workspaceOpen` hook. Prefer **user-level** Cursor MCP so you don’t get two Mycelium servers.

Full matrix + manual snippets: **[docs/MCP-CLIENTS.md](docs/MCP-CLIENTS.md)**.

Quick Claude Code:

```bash
claude mcp add mycelium \
  --env MYCELIUM_CORE_URL=http://127.0.0.1:8787 \
  -- /ABSOLUTE/PATH/TO/mycelium/venv/bin/mycelium-mcp
```

Optional agent rule (Cursor): copy [`templates/cursor/mycelium-mcp.mdc`](templates/cursor/mycelium-mcp.mdc) → `.cursor/rules/`.

### 3. Bootstrap, then ask (relevant-only)

1. Start Core on `:8787` (Desktop or `mycelium serve`) — open a git repo in Cursor to auto-index via `workspaceOpen`
2. Agent calls `mycelium_session_start` with your repo’s absolute path (compact prefs + open-file focus; also indexes if needed)
3. On plan/build: `mycelium_reuse_check` first — ask reuse vs new if strong prior art
4. Prefer `mycelium_change_context` / `mycelium_debug_context` / `mycelium_search` over grepping the whole tree
5. Cite the `receipt=` line; use `mycelium_verify_receipt` to check staleness instead of re-pasting files

| Tool | Role |
|---|---|
| `mycelium_session_start` / `preflight` | Bootstrap + optional index |
| `mycelium_reuse_check` | Cross-repo prior art; ask reuse vs new |
| `mycelium_change_context` | Implement / change a goal |
| `mycelium_debug_context` | Fix an error / stack |
| `mycelium_search` / `focus` | Semantic or file-local recall |
| `mycelium_verify_receipt` | Tiny valid/stale check (paths only) |

Full write/read policy: [docs/AGENT-SECOND-BRAIN.md](docs/AGENT-SECOND-BRAIN.md) · receipts: [docs/superpowers/specs/2026-07-27-context-receipts-design.md](docs/superpowers/specs/2026-07-27-context-receipts-design.md) · ops: [docs/DEPLOY.md](docs/DEPLOY.md#mcp-path-based)

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

- [**Getting started**](docs/GETTING-STARTED.md) — Desktop, Thinking Vault, multi-agent MCP
- [Positioning](docs/POSITIONING.md) — token efficiency vs agent-memory products
- [Marketing / star growth](docs/marketing/) — agent runbook, launch week, paste-ready drafts
- [Deploy / ops](docs/DEPLOY.md) — install, MCP, release gate
- [Connect GitHub](docs/GITHUB.md) — import repos for cross-repo search
- [Agent second brain](docs/AGENT-SECOND-BRAIN.md) — MCP read/write loop
- [MCP clients](docs/MCP-CLIENTS.md) — Cursor, VS Code/Copilot, Codex, Claude, Windsurf
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
