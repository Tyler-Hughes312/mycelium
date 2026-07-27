# Agent second brain (Mycelium)

Mycelium is not only search — agents should **read and write** the Thinking Vault so durable knowledge accumulates locally.

Default folder layout is inspired by [kepano/kepano-obsidian](https://github.com/kepano/kepano-obsidian) (Notes, Daily, References, Templates, Clippings, Attachments) and [breferrari/obsidian-mind](https://github.com/breferrari/obsidian-mind) (brain/, work/, reference/, thinking/, agent filing rules).

## Default vault layout

```text
Home.md                 MOC
AGENTS.md               Where agents should file notes
brain/                  North Star, Key Decisions, Patterns, Gotchas
work/active|archive|decisions
notes/                  Evergreen atomic notes
daily/                  Day logs
reference/              Codebase / architecture maps
thinking/               Scratch (promote then delete)
templates/              Decision / Work / Thinking starters
clippings/              Raw captures
attachments/            Media
```

Scaffolded automatically on Core first run (`ensure_local_layout`) and via `POST /vault/scaffold` / `mycelium_vault_scaffold` (idempotent — never overwrites).

## What ships in the app

| Piece | Role |
|---|---|
| MCP server instructions | Built into `python -m mycelium.bridges.mcp` — hard hooks + read/write guidance |
| Session / preflight | `mycelium_session_start`, `mycelium_preflight` — bootstrap packet |
| Prior-art reuse | `mycelium_reuse_check` — all-repo search; ask reuse vs new before plan/build |
| Task packets | `mycelium_change_context`, `mycelium_debug_context` |
| Write tools | `mycelium_create_bucket`, `mycelium_create_note`, `mycelium_update_note`, `mycelium_vault_scaffold` |
| Read tools | tree / pack / get_note / search / focus / commits |
| Cursor rule template | [`templates/cursor/mycelium-mcp.mdc`](../templates/cursor/mycelium-mcp.mdc) — install copies to `.cursor/rules/` |
| MCP config example | [`templates/cursor/mcp.json.example`](../templates/cursor/mcp.json.example) |
| Cursor `workspaceOpen` hook | [`templates/cursor/hooks.json`](../templates/cursor/hooks.json) — install merges into `~/.cursor/hooks.json`; script at `~/.mycelium/bin/cursor-workspace-open` |

## Hard hooks

1. Start meaningful work with `mycelium_session_start` / `mycelium_preflight` + absolute `workspace_path`.
2. On plan / build / implement intents: `mycelium_reuse_check(goal)` first; if ASK USER, wait for reuse vs new.
3. Before broad exploration, use Mycelium search / focus / change_context / debug_context.
4. Prefer task-shaped tools for implement vs fix intents (after reuse_check when building).
5. No transcript dumps into the vault.

## Zero-config workspaces

Passing an unknown `workspace_path` **auto-registers** a git repo. A **full index** starts from either:

1. **Cursor `workspaceOpen` hook** (user-level, installed by `./scripts/install.sh`) — when you open a git repo in Cursor, Core registers it and starts indexing even with no agent chat. Fail-open if Core is offline.
2. **`mycelium_session_start` / `mycelium_preflight`** when `ensure_index=true` (default).

Search/focus may register but will not start a full index — they hint you to call session_start if the repo looks empty.

## Write policy

**Do write:** decisions, ADRs, “why we chose X”, conventions worth next week, notes linked to symbols with `[[wikilinks]]`.

**Do not write:** every chat turn, raw transcripts, ephemeral debug dumps.

## Index freshness

- Core **watches** registered workspace repos and the vault folder (watchdog).
- `mycelium_search` / `mycelium_focus` call `POST /workspaces/{id}/sync` first (dirty files → incremental reindex; HEAD moved → full async index).
- Vault note create/update re-embeds immediately; disk edits to `.md` also re-embed via vault watcher.
- Explicit: `mycelium_sync_index` after large edit batches.

## Enable for Cursor (any machine)

**Fast path:** Download [Desktop](https://github.com/Tyler-Hughes312/mycelium/releases/tag/v0.1.3-desktop) (Core on `:8787`) + clone repo → `./scripts/install.sh` for `mycelium-mcp` only.

1. Start Core: Desktop app, or `./scripts/dev.sh` / `mycelium serve` on `:8787`
2. `./scripts/install.sh` (venv + project rule/MCP + **user-level** `~/.cursor/hooks.json` `workspaceOpen` + `~/.cursor/mcp.json`)
3. Open any git repo in Cursor — indexing starts via the hook (Core must be up)
4. In Agent chat, call `mycelium_session_start` with the repo’s absolute path for the compact brain/open-file packet

Same MCP works for Claude Code / other MCP clients — they pick up server `instructions` automatically.

See also the README section **Use with Cursor / Claude (MCP)**.
Design: [`docs/superpowers/specs/2026-07-27-agent-context-tools-design.md`](superpowers/specs/2026-07-27-agent-context-tools-design.md).
