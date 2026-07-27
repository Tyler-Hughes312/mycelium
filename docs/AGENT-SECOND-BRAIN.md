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
| MCP server instructions | Built into `python -m mycelium.bridges.mcp` — every connected agent gets read+write guidance |
| Write tools | `mycelium_create_bucket`, `mycelium_create_note`, `mycelium_update_note`, `mycelium_vault_scaffold` |
| Read tools | tree / pack / get_note / search / focus / commits |
| Cursor rule template | [`templates/cursor/mycelium-mcp.mdc`](../templates/cursor/mycelium-mcp.mdc) — install copies to `.cursor/rules/` |
| MCP config example | [`templates/cursor/mcp.json.example`](../templates/cursor/mcp.json.example) |

## Write policy

**Do write:** decisions, ADRs, “why we chose X”, conventions worth next week, notes linked to symbols with `[[wikilinks]]`.

**Do not write:** every chat turn, raw transcripts, ephemeral debug dumps.

## Index freshness

- Core **watches** registered workspace repos and the vault folder (watchdog).
- `mycelium_search` / `mycelium_focus` call `POST /workspaces/{id}/sync` first (dirty files → incremental reindex; HEAD moved → full async index).
- Vault note create/update re-embeds immediately; disk edits to `.md` also re-embed via vault watcher.
- Explicit: `mycelium_sync_index` after large edit batches.

## Enable for Cursor (any machine)

**Fast path:** Download [Desktop](https://github.com/Tyler-Hughes312/mycelium/releases/tag/v0.1.2-desktop) (Core on `:8787`) + clone repo → `./scripts/install.sh` for `mycelium-mcp` only.

1. Start Core: Desktop app, or `./scripts/dev.sh` / `mycelium serve` on `:8787`
2. `./scripts/install.sh` (venv + Cursor rule + MCP example)
3. Copy `templates/cursor/mcp.json.example` → `.cursor/mcp.json` (use absolute `…/venv/bin/mycelium-mcp`)
4. Index a workspace in Desktop → Reload Cursor MCP

Same MCP works for Claude Code / other MCP clients — they pick up server `instructions` automatically.

See also the README section **Use with Cursor / Claude (MCP)**.
