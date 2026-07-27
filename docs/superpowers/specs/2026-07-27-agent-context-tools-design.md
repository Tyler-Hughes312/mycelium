# Agent context tools — design

**Date:** 2026-07-27  
**Status:** Accepted for implementation

## Goal

Close the “agents don’t call MCP / other repos need Desktop first” gap with:

1. Session bootstrap packet (`mycelium_session_start` / `mycelium_preflight`)
2. Hard hooks via MCP instructions + Cursor rule (policy, not runtime enforcement)
3. Zero-config workspace **register** from `workspace_path`; **index** via Cursor `workspaceOpen` hook and/or session_start (`ensure_index=True` default)
4. Task-shaped tools: `mycelium_change_context`, `mycelium_debug_context`

## Non-goals

- Chat journal / auto-dumping transcripts into the vault
- Forcing Cursor to call tools server-side
- Desktop UI for bootstrap
- Bundling MCP into the Desktop installer
- Auto-starting Core when the Cursor hook fires (fail-open if Core is offline)

## Architecture

Compose existing Core HTTP in the MCP bridge (`bridges/mcp/`): register, index, sync, query, focus, vault pack, commits. No new Core domain service required.

**Cursor open-folder path:** user-level `workspaceOpen` hook → stdlib script `~/.mycelium/bin/cursor-workspace-open` → `POST /workspaces` + `POST .../index` (same Core API as Desktop). Independent of MCP being enabled in that project.

## Indexing policy (B+)

- Unknown `workspace_path` → auto-register if git repo
- Full index starts from:
  - Cursor **`workspaceOpen`** hook (folder open / folder change; fail-open if Core down)
  - and/or `mycelium_session_start` / `mycelium_preflight` when `ensure_index=True`
- Search/focus may register but must not start a full index; hint to call session_start if empty
- Re-open of an already `complete` / `running` / `indexing` workspace does not restart a full index

## Tools

| Tool | Role |
|---|---|
| `mycelium_session_start` | Register → maybe index → sync → workspace map → brain pack → focus open files |
| `mycelium_preflight` | Alias with smaller brain token budget |
| `mycelium_reuse_check(goal)` | All-repo prior art; ASK reuse/adapt vs build new when strong hits |
| `mycelium_change_context(goal)` | Ranked packet: search + decisions slice + recent commits |
| `mycelium_debug_context(error)` | Ranked packet: search + optional focus/commits + gotchas slice |

## Hard hooks (agent policy)

1. Start meaningful work with `session_start` / `preflight` + absolute `workspace_path`
2. On plan / build / implement: `reuse_check(goal)` first; if ASK USER, wait
3. Before broad exploration, use Mycelium search/focus/task tools first
4. Prefer task-shaped tools for implement/fix intents (after reuse_check when building)
5. No transcript dumps
