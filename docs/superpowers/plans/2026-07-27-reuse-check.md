# Prior-art reuse check Implementation Plan

> **For agentic workers:** Implement task-by-task. Steps use checkbox syntax.

**Goal:** Add `mycelium_reuse_check` so agents find similar past code across repos and ask reuse vs new before building.

**Architecture:** MCP tool queries Core with `workspace_id='*'`, formats a compact packet via new formatter helpers, and hard-hooks agent instructions/rules to call it before plan/build.

**Tech Stack:** Python MCP bridge, existing `CoreHttp.query`, formatter unit tests.

## Global Constraints

- Always search all workspaces (`*`)
- Fail-open on sync errors
- No Cursor prompt hooks
- Compact packet + receipt; no vault dumps

---

### Task 1: Formatter helpers

**Files:**
- Modify: `services/core/src/mycelium/bridges/mcp/formatters.py`
- Test: `services/core/tests/test_reuse_check.py`

- [ ] Add `is_junk_path`, `is_code_like_hit`, `classify_reuse_hits`, `format_reuse_packet`
- [ ] Unit tests: strong (other repo), strong (2 local), weak/empty

### Task 2: MCP tool + instructions

**Files:**
- Modify: `services/core/src/mycelium/bridges/mcp/server.py`
- Modify: `services/core/src/mycelium/bridges/mcp/README.md`

- [ ] Add `mycelium_reuse_check` tool
- [ ] Update `_INSTRUCTIONS` hard hooks
- [ ] Smoke in existing MCP agent context test if cheap

### Task 3: Rules + docs

**Files:**
- Modify: `templates/cursor/mycelium-mcp.mdc`, `.cursor/rules/mycelium-mcp.mdc`
- Modify: `docs/AGENT-SECOND-BRAIN.md`, `docs/superpowers/specs/2026-07-27-agent-context-tools-design.md`, `CHANGELOG.md`
