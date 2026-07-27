# Prior-art reuse check — design

**Date:** 2026-07-27  
**Status:** Accepted for implementation

## Goal

Before agents plan or build something new, they search **all indexed workspaces** for similar prior work. If strong hits exist, they **ask the user**: reuse/adapt that work, or build greenfield.

## Tool: `mycelium_reuse_check`

| Arg | Default | Role |
|---|---|---|
| `goal` | required | What the user wants to plan/build |
| `workspace_path` | `""` | Current repo path (labels “here” vs “elsewhere”) |
| `workspace_id` | `""` | Unused for query scope; reserved |
| `limit` | `8` | Ranked hit cap |

**Query scope:** always `workspace_id='*'` (all registered repos). That is the reuse wedge.

**Does not** start a full index. Optional sync of current workspace only if `workspace_path` resolves (best-effort, fail-open).

### Packet shape

1. `# Reuse check: {goal}`
2. Ranked hits split into **Other repos** / **This repo** (when current path known)
3. Decision block:
   - Strong → `ASK USER: Reuse/adapt similar work, or build new? Do not implement until they answer.`
   - Weak/empty → `No strong prior art — proceed greenfield.`
4. One-line `receipt=`

### Strong-hit heuristic (v1)

A hit is “code-like” if `kind` is `Symbol`, `File`, or `Function` (case-insensitive), and path does not look like junk (`/target/`, `node_modules`, `.venv`, `_internal/`).

Strong if:

- ≥1 code-like hit from a **different** workspace than current, **or**
- ≥2 code-like hits in the **current** workspace

Otherwise greenfield.

## Agent wiring

Hard hook in MCP `_INSTRUCTIONS` + `templates/cursor/mycelium-mcp.mdc`:

> On plan / build / implement intents: call `mycelium_reuse_check(goal)` **before** `change_context` / coding. If the packet says ASK USER, ask and wait.

`mycelium_change_context` docstring: prefer `reuse_check` first for greenfield builds.

## Non-goals

- Cursor `beforeSubmitPrompt` auto-hook
- Blocking MCP tools until user answers
- Vault write of the choice
- Fixing index junk paths (separate)

## Files

- `services/core/src/mycelium/bridges/mcp/formatters.py` — `classify_reuse_hits`, `format_reuse_packet`
- `services/core/src/mycelium/bridges/mcp/server.py` — tool + instructions
- Tests in `services/core/tests/test_scaffold.py` or `test_reuse_check.py`
- Docs: AGENT-SECOND-BRAIN, MCP README, agent-context design, CHANGELOG, cursor rule
