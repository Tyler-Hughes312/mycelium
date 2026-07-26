# Incremental Index + Soft Note Demotion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep File/Symbol (+ vectors) fresh on FS changes without full reindex, and soft-demote vault Notes in RAG unless the query asks for notes.

**Architecture:** Harden `IndexService.reindex_file` vector hygiene; expose watcher status on `/health`; change `intent_kinds` / `kind_boost` so default queries prefer code. Desktop Search + MCP share `RagService`.

**Tech Stack:** Python Core (`services/core`), pytest, existing watchdog watchers, JsonVectorStore.

**Spec:** `docs/superpowers/specs/2026-07-26-incremental-index-and-soft-note-demotion-design.md`

## Global Constraints

- Soft demote Notes (multiplier **0.55**) when no note intent — do not hard-exclude.
- Note intent includes: note, vault, markdown, decision(s), ADR, “why we”.
- Incremental path updates only; no commit-range incremental in this plan.
- TDD: failing test first for each behavior.

---

## File map

| File | Role |
|---|---|
| `services/core/src/mycelium/core/domain/node_types.py` | `intent_kinds` + `kind_boost` |
| `services/core/src/mycelium/core/domain/index_service.py` | Vector cleanup in `reindex_file` |
| `services/core/src/mycelium/adapters/http/app.py` | `/health` watchers field |
| `services/core/src/mycelium/adapters/git/watcher.py` | Optional `status()` helper |
| `services/core/tests/test_node_types_boost.py` | Unit tests for boost |
| `services/core/tests/test_scaffold.py` (or new) | Delete clears vectors |

---

### Task 1: Soft note demotion

- [x] Write failing unit tests for `kind_boost` / `intent_kinds`
- [x] Implement boost + expanded note patterns
- [x] Verify tests pass

### Task 2: Vector hygiene on reindex_file

- [x] Write failing test: delete via hook removes vectors for that path
- [x] Implement cleanup in `reindex_file` (delete file id + dropped symbol ids)
- [x] Verify tests pass

### Task 3: Watcher health

- [x] Add `WorkspaceWatcherManager.status()` → `{available, workspaces}`
- [x] Include on `/health`
- [x] Test health payload includes watchers

### Task 4: Spec status + dogfood note

- [x] Mark design spec status implemented
- [x] Run focused pytest suite
