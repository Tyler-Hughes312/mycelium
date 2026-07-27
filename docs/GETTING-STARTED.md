# Getting started — Desktop, vault, and coding agents

**Goal:** Core running → Thinking Vault ready → MCP in your IDE(s) → agents get tight packets.

Nothing leaves `localhost`. Indexes and vault live under `~/.mycelium/`.

---

## Easy path (≈5 minutes)

### 1. Install Desktop (Core + vault)

1. Download **0.1.3**: [Desktop release](https://github.com/Tyler-Hughes312/mycelium/releases/tag/v0.1.3-desktop) · [install notes](DESKTOP-INSTALL.md)
2. Launch Mycelium. Core binds `http://127.0.0.1:8787`.
3. On first run, Core **scaffolds the Thinking Vault** at:

   ```text
   ~/.mycelium/vault/
     Home.md · AGENTS.md · brain/ · work/ · notes/ · daily/ · …
   ```

   Open **Vault** in Desktop to browse it. You do **not** create this folder by hand.

4. In **Library**, add a git repo → **Index** (or open the repo in Cursor with the `workspaceOpen` hook — see step 2).

### 2. Wire MCP into your coding agents (one command)

Agents talk to Core through `mycelium-mcp` (stdio). Clone once, then install into every client Mycelium finds:

```bash
git clone https://github.com/Tyler-Hughes312/mycelium.git
cd mycelium
./scripts/install.sh
```

That:

- Creates `venv/` + `mycelium-mcp`
- Merges Mycelium into **Cursor, VS Code/Copilot, Codex, Windsurf, Claude Desktop** (when present)
- Installs Cursor’s **workspaceOpen** hook (open a git folder → register + index)
- Copies the Cursor agent rule into this repo’s `.cursor/rules/`

**Claude Code** (one-liner printed by install):

```bash
claude mcp add mycelium \
  --env MYCELIUM_CORE_URL=http://127.0.0.1:8787 \
  -- /ABSOLUTE/PATH/TO/mycelium/venv/bin/mycelium-mcp
```

Full matrix + manual snippets: **[MCP-CLIENTS.md](MCP-CLIENTS.md)**.

**After install:** reload MCP in your IDE (Cursor: Settings → MCP → refresh, or restart). Prefer **user-level** Cursor MCP only (`user-mycelium`) — avoid a second project entry.

### 3. Use it

| You | Agent |
|---|---|
| Desktop / Core running | `mycelium_session_start` with the repo’s absolute path |
| Plan / build | `mycelium_reuse_check` first — adapt prior art vs greenfield |
| Implement / debug | `mycelium_change_context` / `mycelium_debug_context` / search |
| Durable decisions | Vault in Desktop **or** `mycelium_create_note` — not chat dumps |

Cite the one-line `receipt=` — don’t re-paste the tree. Watch **Impact** on Desktop for grounded %.

Write/read policy: **[AGENT-SECOND-BRAIN.md](AGENT-SECOND-BRAIN.md)**.

---

## What “the vault” is (and isn’t)

| | |
|---|---|
| **Is** | Optional markdown second brain under `~/.mycelium/vault` — decisions, ADRs, conventions. Same disk for Desktop + MCP. |
| **Isn’t** | Auto chat memory / transcript dump. Code index is the product; vault is secondary. |
| **Created when** | First Core start (Desktop or `mycelium serve`). Idempotent scaffold — never overwrites your notes. |

---

## Already developing from source?

```bash
./scripts/install.sh
./scripts/dev.sh          # Core :8787 + Desktop UI
```

Same vault path. Same MCP clients install. See [README](../README.md#develop-from-source-15-minutes).

---

## Checklist

- [ ] Desktop (or Core) healthy: `curl -s http://127.0.0.1:8787/health`
- [ ] `~/.mycelium/vault/Home.md` exists
- [ ] At least one repo indexed (Library or Cursor open-folder)
- [ ] MCP shows ~19 Mycelium tools (including `mycelium_reuse_check`)
- [ ] Agent can run `mycelium_session_start` for your workspace path
