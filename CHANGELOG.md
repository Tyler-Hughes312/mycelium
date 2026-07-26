# Changelog

All notable changes to Mycelium are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Privacy guard helpers (`allow_code_upload` / `allow_remote_llm`) and optional localhost API token
- VS Code `.vsix` packaging via `npm run package`
- Desktop production preview (`scripts/run-desktop.sh`) and deploy runbook (`docs/DEPLOY.md`)
- PATH-based MCP config templates (no `PYTHONPATH` required after install)

### Changed

- Version bumped from 0.0.1 → 0.1.0 across Core, Desktop, UI, and VS Code extension
