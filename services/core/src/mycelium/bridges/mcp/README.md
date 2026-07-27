# Mycelium MCP Bridge

Exposes the same Core Graph/RAG/Vault to AI agents via [Model Context Protocol](https://modelcontextprotocol.io/) (FR-22 / AD-3).

Requires **Core running** on `http://127.0.0.1:8787` (default).

**Easiest:** open the **Mycelium desktop app** — it starts Core and leaves it running
after you quit, so MCP keeps working.

**Otherwise:**

```bash
./scripts/ensure-core.sh   # starts Core only if /health is down
# or
./scripts/run-core.sh
```

## Run (stdio)

```bash
# after: pip install -e services/core
mycelium-mcp
```

Or from a repo venv:

```bash
./venv/bin/mycelium-mcp
```

Env:

| Variable | Default | Meaning |
|---|---|---|
| `MYCELIUM_CORE_URL` | `http://127.0.0.1:8787` | Core HTTP base |

When the MCP client sends a recognizable model id in request `_meta` (e.g. `model`, `model_id`), the bridge forwards it to Core as `X-Mycelium-Model-Id` for Impact cost estimates. If no model is present — common in Cursor today — Core falls back to your Settings **Impact default model** (`Assumed` badge in Desktop).

## Tools

| Tool | Purpose |
|---|---|
| `mycelium_health` | Core reachability |
| `mycelium_list_workspaces` | Registered repos |
| `mycelium_session_start` | Session bootstrap (register + optional index + brain pack + open-file focus) |
| `mycelium_preflight` | Thin alias of session_start (smaller brain budget) |
| `mycelium_reuse_check` | Cross-repo prior art before plan/build — ASK reuse vs new when strong hits |
| `mycelium_verify_receipt` | Check receipt valid/stale — paths/titles only, no bodies |
| `mycelium_change_context` | Task packet for implementing a change |
| `mycelium_debug_context` | Task packet for fixing an error |
| `mycelium_search` | Hybrid RAG across **all** indexed repos by default (or one workspace) |
| `mycelium_focus` | Focus packet for path / symbol / line |
| `mycelium_vault_tree` | Folder/bucket map (no RAG) — prefer first |
| `mycelium_vault_pack` | Token-budget pack for a bucket (no RAG) |
| `mycelium_get_note` | Vault note by id/title (same disk as Desktop) |
| `mycelium_create_bucket` | New vault folder + `_index.md` |
| `mycelium_create_note` | Write a durable vault note (second brain) |
| `mycelium_update_note` | Update an existing vault note |
| `mycelium_vault_scaffold` | Ensure kepano/obsidian-mind layout (idempotent) |
| `mycelium_sync_index` | Sync dirty code files + optional vault reindex |
| `mycelium_commits_for_path` | Commits touching a path |

**Hard hooks:** call `mycelium_session_start` / `mycelium_preflight` at the start of meaningful work; on plan/build call `mycelium_reuse_check` first (ask reuse vs new if strong hits); use search/focus/task tools before broad grepping. Packets end with a one-line `receipt=` — cite it; use `mycelium_verify_receipt` instead of re-dumping. Unknown `workspace_path` auto-registers. Full index starts from the Cursor **`workspaceOpen` hook** (open folder → register + index) and/or `session_start` / `preflight` when `ensure_index=true`.

**Read (token-saving):** session bootstrap → `mycelium_vault_tree` → `mycelium_vault_pack(bucket)` → `mycelium_get_note` only if needed.

**Write (when necessary):** durable decisions / ADRs with `[[wikilinks]]` — not every chat turn. See `docs/AGENT-SECOND-BRAIN.md`.

## Cursor

Prefer PATH / absolute binary (**no `PYTHONPATH`**):

```json
{
  "mcpServers": {
    "mycelium": {
      "command": "mycelium-mcp",
      "env": {
        "MYCELIUM_CORE_URL": "http://127.0.0.1:8787"
      }
    }
  }
}
```

If the IDE does not see your shell PATH, set `command` to `…/venv/bin/mycelium-mcp`.

`./scripts/install.sh` also merges Mycelium into **user-level** `~/.cursor/mcp.json` and installs a `workspaceOpen` hook (`~/.mycelium/bin/cursor-workspace-open`) so opening any git repo registers + indexes against Core (fail-open if Core is down). Template: `templates/cursor/hooks.json`.

See `templates/cursor/mcp.json.example` and `docs/DEPLOY.md`.

## Claude Code

```bash
claude mcp add mycelium -- mycelium-mcp
```

## Agent tip

1. `mycelium_list_workspaces` → pick `workspace_id`
2. `mycelium_search` with a natural-language question
3. `mycelium_focus` when you know a file/symbol
4. `mycelium_get_note` for Vault decisions
