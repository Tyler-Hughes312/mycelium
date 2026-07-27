# Mycelium MCP — IDE & agent clients

One stdio server (`mycelium-mcp`) talks to local Core on `http://127.0.0.1:8787`.  
Wire that binary into whichever coding agent you use — **same tools everywhere** (index + Thinking Vault).

**New here?** Start with **[GETTING-STARTED.md](GETTING-STARTED.md)** (Desktop → vault → agents).

**Prerequisite:** Core running (Desktop app or `./scripts/run-core.sh`). First Core start scaffolds `~/.mycelium/vault/` automatically.

**One-command install** (preferred — `./scripts/install.sh` already does this):

```bash
./scripts/install.sh
# or only the client merge:
./venv/bin/python scripts/install_mcp_clients.py \
  --repo-root "$(pwd)" \
  --mycelium-mcp "$(pwd)/venv/bin/mycelium-mcp"
```

That merges Mycelium into every client it can find on your machine and installs the Cursor `workspaceOpen` auto-index hook.

---

## Client matrix

| Client | Config location | Root key | Install notes |
|---|---|---|---|
| **Cursor** | `~/.cursor/mcp.json` (user) | `mcpServers` | Prefer **user-level only** — avoid also putting Mycelium in project `.cursor/mcp.json` (duplicates) |
| **Cursor hooks** | `~/.cursor/hooks.json` | `workspaceOpen` | Auto-register + index when you open a git repo |
| **VS Code + Copilot** | User: `…/Code/User/mcp.json` · Workspace: `.vscode/mcp.json` | `servers` (+ `"type": "stdio"`) | Use **Agent** mode; reload window after install |
| **VS Code Insiders** | `…/Code - Insiders/User/mcp.json` | same | Installed if Insiders is present |
| **OpenAI Codex** (CLI / IDE) | `~/.codex/config.toml` | `[mcp_servers.mycelium]` | Also: `codex mcp add mycelium -- ./venv/bin/mycelium-mcp` |
| **Claude Code** | CLI registry | — | `claude mcp add mycelium --env MYCELIUM_CORE_URL=http://127.0.0.1:8787 -- /ABS/venv/bin/mycelium-mcp` |
| **Claude Desktop** | `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) | `mcpServers` | Only if Claude Desktop is installed |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` | `mcpServers` | Cascade / agent chat |
| **Mycelium VS Code extension** | Extension settings | HTTP to Core | Side panel Context + New Note — complementary to MCP |

Templates under `templates/`:

- [`templates/cursor/mcp.json.example`](../templates/cursor/mcp.json.example)
- [`templates/vscode/mcp.json.example`](../templates/vscode/mcp.json.example)
- [`templates/codex/mcp_servers.mycelium.toml.snippet`](../templates/codex/mcp_servers.mycelium.toml.snippet)
- [`templates/windsurf/mcp_config.json.example`](../templates/windsurf/mcp_config.json.example)
- [`templates/claude-desktop/claude_desktop_config.snippet.json`](../templates/claude-desktop/claude_desktop_config.snippet.json)

---

## Avoid two Mycelium servers in Cursor

Cursor loads **both** `~/.cursor/mcp.json` and project `.cursor/mcp.json`.  
`install_mcp_clients.py` writes the **user** config and **removes** `mycelium` from the project file by default.

To keep a project-only entry: `--keep-project-cursor-mcp`.

**After install / tool changes:** reload MCP in Cursor (MCP panel refresh or restart Cursor). A stale `mycelium-mcp` process will miss new tools (`mycelium_reuse_check`) and agents may error with “server does not exist” if they still target an old `project-…-mycelium` id — the live id is usually `user-mycelium`.

**If tools time out:** check Desktop/Library — a stuck full index pegs Core CPU. Cancel index or restart Core (`./scripts/run-core.sh` / relaunch Desktop).

---

## Manual snippets

### Cursor / Windsurf / Claude Desktop

```json
{
  "mcpServers": {
    "mycelium": {
      "command": "/ABS/PATH/venv/bin/mycelium-mcp",
      "args": [],
      "env": { "MYCELIUM_CORE_URL": "http://127.0.0.1:8787" }
    }
  }
}
```

### VS Code / GitHub Copilot

```json
{
  "servers": {
    "mycelium": {
      "type": "stdio",
      "command": "/ABS/PATH/venv/bin/mycelium-mcp",
      "args": [],
      "env": { "MYCELIUM_CORE_URL": "http://127.0.0.1:8787" }
    }
  }
}
```

### Codex

```toml
[mcp_servers.mycelium]
command = "/ABS/PATH/venv/bin/mycelium-mcp"
args = []
startup_timeout_sec = 30

[mcp_servers.mycelium.env]
MYCELIUM_CORE_URL = "http://127.0.0.1:8787"
```

### Claude Code

```bash
claude mcp add mycelium \
  --env MYCELIUM_CORE_URL=http://127.0.0.1:8787 \
  -- /ABS/PATH/venv/bin/mycelium-mcp
```

---

## Agent loop (all clients)

1. `mycelium_session_start` with absolute `workspace_path`
2. Plan/build → `mycelium_reuse_check` (ask reuse vs new if strong hits)
3. `mycelium_change_context` / `mycelium_debug_context` / `mycelium_search`
4. Cite `receipt=` — don’t re-dump the repo

Cursor rule template: [`templates/cursor/mycelium-mcp.mdc`](../templates/cursor/mycelium-mcp.mdc)  
Policy: [`docs/AGENT-SECOND-BRAIN.md`](AGENT-SECOND-BRAIN.md)
