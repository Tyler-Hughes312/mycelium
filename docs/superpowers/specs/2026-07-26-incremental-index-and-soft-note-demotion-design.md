# Incremental Index Freshness + Soft Note Demotion — Design Spec

**Date:** 2026-07-26  
**Status:** Implemented  
**Binds:** FR-4 (continuous incremental update), AD-4 (hybrid retrieval), Story 2.5  
**Scope:** Core Service indexing freshness + RAG ranking (Desktop Search + MCP share the same path)
**Plan:** `docs/superpowers/plans/2026-07-26-incremental-index-and-soft-note-demotion.md`

## Goal

1. **Keep the graph fresh without full reindex** — after Initial Index, create/modify/delete of source files updates File/Symbol nodes (and embeddings) for **only those paths**.
2. **Prefer live code in RAG** — when agents/users ask about code, Symbols/Files rank above vault Notes unless the query clearly asks for notes/decisions.

**Success:**
- Edit a tracked `.py`/`.ts` file → symbols for that path refresh within ~1s (debounced watcher), no “Run Index”.
- Delete that file → symbols **and** vectors for that path are gone; search no longer returns them.
- Query like “how does workspace registration work?” → top hits are Symbol/File with paths/lines; Notes may appear lower.
- Query like “why did we choose local-first?” / “vault decision” → Notes boosted again.

**Out of scope (this spec):**
- Making **HEAD/commit** advances incremental (still may trigger full index today). Track separately if needed.
- Changing Desktop “Run Index” (remains explicit full rebuild).

## Approach (locked)

**Harden existing watcher + soft demote Notes in `kind_boost`.**

Not chosen: git-poll-only sync · hard-excluding Notes from MCP search.

---

## Section 1 — Live incremental index

### Current state

| Piece | Status |
|---|---|
| `WorkspaceWatcherManager` (watchdog, debounced) | Exists; starts on Core boot + workspace register |
| `POST .../hooks/file-changed` → `IndexService.reindex_file` | Exists; delete removes File/Symbol JSON nodes |
| MCP/search `sync` dirty working tree | Exists (incremental per dirty path) |
| Vector cleanup on delete / symbol drop | **Gap** — orphans can keep stale code in RAG |
| Watcher observability | **Gap** — no `/health` field for “watching N workspaces” |

### Behavior

```text
FS event (create|modify|delete|move)
  → debounce 350ms
  → reindex_file(workspace_id, path)
       if missing: drop File + Symbols for path + delete their vectors
       if present: upsert File + Symbols for path + re-embed those symbols
                   (also delete vectors for symbol IDs no longer on that path)
```

### Changes

1. **`reindex_file` vector hygiene**  
   After symbol/file upsert or delete, remove vectors for:
   - `file:{path}` when deleted
   - any prior `symbol:…` IDs for that path that are no longer present  
   Use `JsonVectorStore.delete` (already exists).

2. **Health surface**  
   Extend `/health` (or a small nested object) with e.g.:
   ```json
   "watchers": { "available": true, "workspaces": 2 }
   ```
   Desktop can show “Watching” vs “Watcher unavailable” without a new page.

3. **Tests**
   - Existing hook test (modify + delete symbols) stays.
   - Add: after delete, vector store has no rows for that path’s file/symbol ids.
   - Add: unit/integration that `kind_boost` / ranking demotes Notes (Section 2).
   - Optional: short watcher test if feasible without flaky sleeps; otherwise hook path is the contract.

### Non-goals for Section 1

- Replacing full index when user clicks Run Index.
- Commit-range incremental indexing when HEAD moves.

---

## Section 2 — Soft note demotion (B)

### Current state

`intent_kinds()` only boosts when query words match (`file`, `function`, `note`, …).  
Most agent queries have **empty intents** → Notes compete 1:1 with code and often win on hashing embeddings / long note text.

### Ranking policy

| Situation | Note multiplier | Symbol / File |
|---|---|---|
| No note intent (default) | **0.55** | **1.0** (existing code-intent boosts still apply when those words appear) |
| Explicit note intent (`note`, `vault`, `markdown`, `decision`, `ADR`, `why we`) | **1.35** | soft penalty ~0.82 if only note family intended |
| Explicit code-only intent | Notes use soft penalty path (fam not in intents) | boosted |

Implement primarily in `kind_boost()` / `intent_kinds()` in `node_types.py` so **Desktop Search and MCP** stay aligned (AD-3 / AD-4).

Expand note-intent patterns: `\bdecisions?\b`, `\bADR\b`, `\bwhy we\b`, keep existing note/vault/markdown.

Provenance already carries `intent_kinds`; no API shape change required.

### Tests

- Unit: `kind_boost("Note", set()) == 0.55`; `kind_boost("Function", set()) == 1.0`
- Unit: note-intent query boosts Note above default
- Integration (optional): after indexing a symbol + creating an overlapping-title note, code-ish query ranks Symbol/File above Note

---

## Error handling

- Watcher failures stay logged; one bad file must not stop the debounce flush loop.
- If `watchdog` missing in a broken install, health reports `available: false`; incremental still works via `file-changed` hook and MCP `sync`.

## Testing summary

| Layer | What |
|---|---|
| Unit | `kind_boost` / `intent_kinds`; vector delete helper if extracted |
| API | file-changed delete clears vectors |
| Manual dogfood | Edit file in registered workspace → Search finds new symbol without Run Index |

## Open follow-ups (not this PR)

- Incremental commit catch-up when HEAD moves (diff vs `indexed_commit` only).
- Desktop UI badge for watcher status (consumes health field).
