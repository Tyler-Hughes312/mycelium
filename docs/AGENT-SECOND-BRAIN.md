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

## Mycelium Chat (RAG conversation window)

Desktop **Chat** is optional and separate from Cursor. Each model call is assembled from system prefs + a small recent-turn tail + RAG-selected thread/code slices — **never** the full transcript. Impact records these as `tool=chat`. Enable remote LLM in Settings (`allow_remote_llm` + `MYCELIUM_LLM_API_KEY` or `~/.mycelium/llm_api_key`). Mycelium does **not** rewrite Cursor’s conversation window; curated vault handoff stays under `work/active/`, not chat dumps.

## Index freshness

- Core **watches** registered workspace repos and the vault folder (watchdog).
- `mycelium_search` / `mycelium_focus` call `POST /workspaces/{id}/sync` first (dirty files → incremental reindex; HEAD moved → full async index).
- Vault note create/update re-embeds immediately; disk edits to `.md` also re-embed via vault watcher.
- Explicit: `mycelium_sync_index` after large edit batches.

## Enable for Cursor / VS Code / Codex / Claude (any machine)

**Start here:** **[GETTING-STARTED.md](GETTING-STARTED.md)** — Desktop scaffolds the vault; one `./scripts/install.sh` wires MCP into your agents.

**Fast path:**

1. Download [Desktop](https://github.com/Tyler-Hughes312/mycelium/releases/tag/v0.1.4-desktop) (Core on `:8787`) — vault appears at `~/.mycelium/vault/`
2. Clone this repo → `./scripts/install.sh` — venv + **MCP into Cursor / VS Code / Codex / Windsurf / Claude Desktop** + Cursor `workspaceOpen` hook
3. Claude Code: `claude mcp add mycelium --env MYCELIUM_CORE_URL=http://127.0.0.1:8787 -- …/venv/bin/mycelium-mcp`
4. Open a git repo (Cursor auto-indexes) → agents call `mycelium_session_start` / `reuse_check`

Client matrix: [`docs/MCP-CLIENTS.md`](MCP-CLIENTS.md).

Same MCP works for any MCP host that can spawn a stdio server.
