# Mycelium — Project Context (planning freeze)

Last updated: 2026-07-25 (desktop-app scope change)

## Product

**Mycelium** — local-first Context Layer for AI-heavy developers:
- Auto Knowledge Graph from code + git
- Local RAG/embeddings
- Obsidian-style Thinking Vault
- **Full Desktop App** (primary human UI)
- VS Code/Cursor Side Panel (in-flow Context)
- MCP for agents

## Canonical planning artifacts

- Change proposal: `_bmad-output/planning-artifacts/sprint-change-proposal-2026-07-25.md`
- Brief / PRD / Architecture / Epics under `_bmad-output/planning-artifacts/`
- UX workspace: `_bmad-output/planning-artifacts/ux/ux-mycelium-2026-07-25/`
- Design handoff prompt: `.../ux/ux-mycelium-2026-07-25/DESIGN-HANDOFF-PROMPT.md`

## Invariants

- Single Core Service owns ranking/indexing (AD-1)
- Local-first; no code upload by default (AD-2)
- One Graph Store for Desktop + editor + MCP (AD-3)
- Hybrid retrieval (AD-4)
- Vault = plain markdown on disk (AD-5)
- Desktop = full console; Editor = focus Context + quick Note; shared `@mycelium/ui` (AD-9)
- Desktop shell lean: **Tauri 2** (confirm vs Electron)

## Next planning step

Run `bmad-ux` with **Design handoff** → external UI AI (Stitch / Figma Make / Galileo) → import mocks → finalize DESIGN.md + EXPERIENCE.md
