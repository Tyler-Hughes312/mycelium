# Mycelium

[![CI](https://github.com/Tyler-Hughes312/mycelium/actions/workflows/ci.yml/badge.svg)](https://github.com/Tyler-Hughes312/mycelium/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-0ea5e9.svg)](CHANGELOG.md)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-3776AB.svg)](services/core/pyproject.toml)
[![Local-first](https://img.shields.io/badge/privacy-local--first-22c55e.svg)](docs/DEPLOY.md)

**Local-first Context Layer** for AI-heavy developers.

One Graph powers Desktop, VS Code/Cursor, and MCP — your code and Thinking Vault stay on `127.0.0.1`. No cloud account.

```text
  Cursor / Claude ──MCP──► mycelium-mcp ──► Core :8787
  Desktop (Vite)  ──HTTP──────────────────► Core :8787
  VS Code panel   ──HTTP──────────────────► Core :8787
                         │
                         ├── ~/.mycelium/vault
                         └── ~/.mycelium/data (indexes)
```

## Why Mycelium

| | |
|---|---|
| **Private by default** | Binds localhost only; upload / remote LLM are opt-in |
| **One brain, three surfaces** | Desktop console · editor side panel · agent MCP tools |
| **Durable memory** | Markdown vault with buckets, wikilinks, and local embeddings |
| **Ship-ready locally** | `pip` / `mycelium serve` · `.vsix` · one-command install |

## Download Desktop

Install a packaged app (Core is bundled — no Python/Node required):

- **Releases:** https://github.com/Tyler-Hughes312/mycelium/releases  
- **Install notes (Gatekeeper / SmartScreen):** [docs/DESKTOP-INSTALL.md](docs/DESKTOP-INSTALL.md)

Build locally on this machine:

```bash
./scripts/package-desktop.sh   # → .dmg / .app under apps/desktop/src-tauri/target/release/bundle/
```

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
  <sub>Built for developers who want AI context without uploading their repo.</sub>
</p>
