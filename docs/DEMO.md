# Mycelium demo script (Epic 8.3)

**Goal:** one visceral “aha” — Desktop search, Side Panel, and MCP all surface the planted rate-limit Context.

## Prerequisites

```bash
./scripts/install.sh
./scripts/dev.sh   # Core :8787 + Desktop :5173
```

Fixture path: `fixtures/dogfood-rate-limits` (created by install / `prepare_dogfood.sh`).

## Aha path (~5 minutes)

### 1. Desktop — Library + Index

1. Open http://localhost:5173 → **Library**
2. Add workspace: absolute path to `fixtures/dogfood-rate-limits`
3. **Index** → Start index → wait until complete (symbols + commits + vectors)

### 2. Desktop — Vault note (planted thinking)

1. **Vault** → New note
2. Title: `Rate limit retries — decision`
3. Body:

```markdown
After reviewing [[authenticate]], we decided on jittered backoff via [[calculate_jitter]]
so rate limiting does not cause thundering herds during recovery.
```

4. Confirm backlinks / unresolved resolve after save (reindex vault if needed via API `POST /vault/reindex`)

### 2b. Vault buckets (structure path, no RAG)

1. **Vault** → create bucket `decisions` (folder+)
2. Edit `decisions/_index.md` brief: one-paragraph summary of rate-limit decisions
3. Create note inside that bucket (or move decision note under it)
4. MCP (optional): `mycelium_vault_tree` → `mycelium_vault_pack` bucket=`decisions` — expect map + index without calling search
5. Agent write-back: `mycelium_create_note` for a durable ADR (see `docs/AGENT-SECOND-BRAIN.md`)

### 3. Desktop — Search

Query: **`how did we handle rate limits`**

Expect: **Function** (`rate_limit_middleware` / `calculate_jitter`), **Commit** (rate limit middleware), and/or **Note** (decision).

### 4. Editor Side Panel

1. Open `apps/vscode` → F5
2. Open `fixtures/dogfood-rate-limits/src/ratelimit.py`
3. Cursor on `calculate_jitter`
4. Mycelium **Context** panel → Refresh

Expect: related symbols / note with explicit link boost.

### 5. MCP

With Core up and MCP configured (`.cursor/mcp.json.example`):

1. `mycelium_list_workspaces`
2. `mycelium_vault_tree` then `mycelium_vault_pack` (structure, no RAG)
3. `mycelium_search` query=`how did we handle rate limits`
4. `mycelium_get_note` note=`Rate limit retries — decision`

Expect: same planted Context as Desktop (no separate agent DB).

## Success criteria

- [ ] Search returns planted rate-limit Context
- [ ] Side Panel shows focus packet for `ratelimit.py`
- [ ] MCP search/note return the Vault decision
- [ ] Privacy: Settings still shows local-first / no cloud account
