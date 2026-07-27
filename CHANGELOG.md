# Changelog

All notable changes to Mycelium are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Mycelium Chat RAG window** — Desktop Chat + Core `/threads` assemble each model call from prefs + recent tail + ranked thread/code hits (never the full transcript). Cursor’s conversation window is not rewritten. Settings: `allow_remote_llm`, OpenAI-compatible base URL / model, API key via `MYCELIUM_LLM_API_KEY` or `~/.mycelium/llm_api_key`. Impact lists `tool=chat` savings.
- **`docs/GETTING-STARTED.md`** — Desktop → Thinking Vault scaffold → one-command multi-agent MCP; linked from README, DESKTOP-INSTALL, MCP-CLIENTS, marketing Setup
- Multi-client MCP install — Cursor, VS Code/Copilot, Codex, Windsurf, Claude Desktop via `scripts/install_mcp_clients.py`; matrix in `docs/MCP-CLIENTS.md`
- Dedupes Cursor project vs user Mycelium MCP by default (one server, not two)
- Marketing site Setup copy: vault auto-scaffold + wire agents across IDEs; Getting started link
- `release-check.sh` also runs marketing site test + production build
- Opt-in marketing publisher (`services/marketing`, `scripts/marketing-publish.sh`) — HN/Reddit drafts with credentials; not required for product install

### Changed

- Marketing site + README + positioning: Desktop Chat RAG window (honest: does not rewrite Cursor’s host transcript)
- `install.sh` / `install_cursor_user_config.py` delegate to multi-client installer; post-install points at GETTING-STARTED
- Design spec `docs/superpowers/specs/2026-07-27-rag-conversation-window-design.md` status → Accepted

## [0.1.3] — 2026-07-27

### Added

- Cursor **`workspaceOpen` hook** — open any git repo → auto-register + start index via Core (user-level `~/.cursor/hooks.json` + `~/.mycelium/bin/cursor-workspace-open`; fail-open if Core down). `./scripts/install.sh` also merges user-level MCP.
- **`mycelium_reuse_check`** — cross-repo prior-art packet before plan/build; agents ask reuse/adapt vs greenfield when strong hits
- Marketing site + README + positioning aligned to open→index, reuse_check, and receipt agent loop
- Agent context tools: `mycelium_session_start` / `preflight`, `change_context` / `debug_context`, zero-config workspace register
- **Context receipts** — compact `receipt=` attestation on Search/Focus/Pack; `mycelium_verify_receipt`; Impact **grounded %**

### Changed

- Version bump 0.1.2 → 0.1.3 (Core, Desktop, UI)

## [0.1.2] — 2026-07-27

### Added

- Desktop **Impact** cost estimates: tokens saved × configured $/1M input, with Assumed / Inferred / Unknown model labels
- Settings: default impact model + custom $/1M rates; Core `/impact/pricing` + `X-Mycelium-Model-Id` probe
- Marketing site token-efficiency positioning (`apps/web`, getmycelium.vercel.app)

### Changed

- Version bump 0.1.1 → 0.1.2 (Core, Desktop, UI)

## [0.1.1] — 2026-07-26

### Fixed

- Desktop first-open race: wait for Core health before mounting pages that fetch data
- Incremental file delete/replace now purges orphan embedding vectors so RAG stays fresh
- Soft-demote vault Notes in hybrid RAG unless the query asks for notes/decisions (code-first for agents)

### Added

- `/health.watchers` status (`available`, `workspaces`) and Desktop “Watching N” indicator

## [0.1.0] — 2026-07-26

### Added

- Production-ready local product packaging: `mycelium serve`, `mycelium-core`, `mycelium-mcp` console scripts
- GitHub Actions CI (Core pytest, Desktop lint+build, VS Code compile)
- MIT LICENSE, release checklist (`scripts/release-check.sh`)
- Structured logging to stderr and `~/.mycelium/logs/`
- Global FastAPI exception handler; `config_version` with migrate-on-load
