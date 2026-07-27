# RAG Conversation Window Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Mycelium Chat where each model call uses only system prefs + a small turn tail + RAG-selected thread/code slices — never the full transcript.

**Architecture:** Core owns threads/turns/chunks, thread-scoped hybrid retrieval, prompt assembly, opt-in LLM calls, receipts, and Impact. Desktop adds a Chat surface that displays the full transcript for humans while showing a **Context used** receipt of what the model actually saw. Vault handoff remains curated (`work/active/`), not a chat dump.

**Tech Stack:** Python 3.12 Core (FastAPI, existing JsonVectorStore / RagService / VaultService / ImpactService), Desktop React + Tauri (existing `apps/desktop` patterns), user-supplied LLM key + `allow_remote_llm`.

**Spec:** `docs/superpowers/specs/2026-07-27-rag-conversation-window-design.md`

## Global Constraints

- Assembled prompt ⊆ system prefs ∪ recent tail ∪ RAG hits — **never** concatenate the full thread
- Defaults: tail ≤ ~400 tokens (k=1–2), thread RAG ≤ ~1500, code/vault RAG ≤ ~1500; drop lowest-ranked hits when over hard cap
- Thread corpus is Core Graph/vector data (`ThreadChunk`); Thinking Vault stays curated — no raw transcript dumps
- Remote LLM requires `allow_remote_llm` + user API key; missing key → block send (`llm_not_configured`)
- Stale/missing embeddings → tail-only + `reason=index_stale` on receipt; never full-thread fallback
- Receipts stay attestation-only (ids/paths/titles + budgets) — no second body dump
- Do not claim Cursor conversation windows are fixed (v1)
- Errors: `{ "error": { "code": "snake_case", "message": "..." } }`

## File map

| Path | Responsibility |
| --- | --- |
| `services/core/src/mycelium/adapters/store/thread_store.py` | Persist threads + turns (JSON under `data/threads/`) |
| `services/core/src/mycelium/core/domain/thread_chunking.py` | Split turn text into embeddable chunks + ids |
| `services/core/src/mycelium/core/domain/chat_assembler.py` | Budgeted prompt assembly (invariant) |
| `services/core/src/mycelium/core/ports/llm.py` | LLM port protocol |
| `services/core/src/mycelium/adapters/llm/echo.py` | Test/dev echo provider |
| `services/core/src/mycelium/adapters/llm/openai_compatible.py` | Opt-in HTTP chat completions |
| `services/core/src/mycelium/core/domain/chat_service.py` | Create thread, append message, retrieve, assemble, call LLM, persist, receipt, impact |
| `services/core/src/mycelium/core/domain/node_types.py` | Add `ThreadChunk` family/display |
| `services/core/src/mycelium/core/domain/rag_service.py` | Title/snippet + optional kind filter for ThreadChunk; thread-scoped query helper |
| `services/core/src/mycelium/core/domain/impact_service.py` | `record_chat_turn(...)` |
| `services/core/src/mycelium/adapters/http/app.py` | `/threads*` routes + wire ChatService |
| `services/core/src/mycelium/core/config.py` | Optional `[llm]` section (provider, model, api_key_env / key file path) |
| `apps/desktop/src/api/client.ts` | Thread API client types + functions |
| `apps/desktop/src/pages/ChatPage.tsx` | Thread list, transcript, composer, Context used |
| `apps/desktop/src/components/AppShell.tsx` / `App.tsx` | Nav + route |
| `apps/desktop/src/pages/SettingsPage.tsx` | LLM enable + key + budgets |
| `services/core/tests/test_chat_*.py` | Unit/integration tests |

---

### Task 1: Thread store + chunking

**Files:**
- Create: `services/core/src/mycelium/adapters/store/thread_store.py`
- Create: `services/core/src/mycelium/core/domain/thread_chunking.py`
- Test: `services/core/tests/test_thread_store.py`

**Interfaces:**
- Produces:
  - `ThreadStore(path: Path)` with `create`, `get`, `list`, `append_turn`, `list_turns`
  - `chunk_turn(*, thread_id: str, seq: int, role: str, text: str, max_chars: int = 800) -> list[dict]`
  - Chunk id: `node:thread_chunk:{thread_id}:{seq}:{i}`

- [ ] **Step 1: Write failing tests**

```python
# services/core/tests/test_thread_store.py
from pathlib import Path
from mycelium.adapters.store.thread_store import ThreadStore
from mycelium.core.domain.thread_chunking import chunk_turn


def test_create_and_append_turn(tmp_path: Path) -> None:
    store = ThreadStore(tmp_path / "threads")
    t = store.create(workspace_id="ws1", title="Demo")
    assert t["id"].startswith("thread:")
    turn = store.append_turn(t["id"], role="user", text="hello")
    assert turn["id"] == f"turn:{t['id']}:1"
    assert turn["seq"] == 1
    turns = store.list_turns(t["id"])
    assert len(turns) == 1
    assert store.get(t["id"])["turn_count"] == 1


def test_chunk_turn_splits_long_text() -> None:
    text = ("word " * 500).strip()
    chunks = chunk_turn(thread_id="thread:abc", seq=1, role="user", text=text, max_chars=100)
    assert len(chunks) >= 2
    assert chunks[0]["id"] == "node:thread_chunk:thread:abc:1:0"
    assert all(c["kind"] == "ThreadChunk" for c in chunks)
    assert all(c["meta"]["thread_id"] == "thread:abc" for c in chunks)


def test_append_turn_idempotent_seq(tmp_path: Path) -> None:
    store = ThreadStore(tmp_path / "threads")
    t = store.create(workspace_id="ws1", title="Demo")
    a = store.append_turn(t["id"], role="user", text="a")
    b = store.append_turn(t["id"], role="assistant", text="b")
    assert a["seq"] == 1 and b["seq"] == 2
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd services/core && python -m pytest tests/test_thread_store.py -v
```

Expected: import / not found errors.

- [ ] **Step 3: Implement store + chunking**

```python
# thread_store.py — JSON files: data/threads/{id_slug}.json + index.json
# Each thread doc: {id, workspace_id, title, created_at, updated_at, handoff_path?, turns: [...]}
# append_turn assigns seq = len(turns)+1, token_est via vault_service.estimate_tokens

# thread_chunking.py
def chunk_turn(*, thread_id, seq, role, text, max_chars=800) -> list[dict]:
    # split on whitespace into <= max_chars pieces; empty text → one empty chunk skipped
    # return [{id, kind:"ThreadChunk", text, meta:{thread_id, turn_seq, role, chunk_i}}]
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd services/core && python -m pytest tests/test_thread_store.py -v
```

- [ ] **Step 5: Commit**

```bash
git add services/core/src/mycelium/adapters/store/thread_store.py \
  services/core/src/mycelium/core/domain/thread_chunking.py \
  services/core/tests/test_thread_store.py
git commit -m "feat(core): add thread store and turn chunking"
```

---

### Task 2: Prompt assembler (invariant)

**Files:**
- Create: `services/core/src/mycelium/core/domain/chat_assembler.py`
- Test: `services/core/tests/test_chat_assembler.py`

**Interfaces:**
- Consumes: turn dicts `{seq, role, text, token_est?}`, RAG hit dicts `{id, kind, path, title, snippet, score, token_est?}`
- Produces: `assemble_chat_prompt(...) -> dict` with keys:
  - `messages: list[{role, content}]` (OpenAI-style)
  - `included_turn_seqs: set[int]`
  - `included_hit_ids: list[str]`
  - `tokens_assembled: int`
  - `tokens_full_thread_est: int`
  - `tokens_saved_est: int`
  - `budgets: dict`
  - `truncated: bool`
  - `reason: str | None` (e.g. `index_stale`)

```python
def assemble_chat_prompt(
    *,
    system_text: str,
    all_turns: list[dict],
    query_text: str,
    thread_hits: list[dict],
    code_hits: list[dict],
    tail_k: int = 2,
    tail_token_budget: int = 400,
    thread_rag_budget: int = 1500,
    code_rag_budget: int = 1500,
    hard_cap: int = 4000,
) -> dict: ...
```

**Rules:**
1. Always include `system` message from `system_text` (truncate system to ≤600 tokens if needed).
2. Tail = last `tail_k` turns by seq, trimmed to `tail_token_budget` (drop oldest of the tail first).
3. Fill thread hits by descending score until `thread_rag_budget`; skip any hit whose `meta.turn_seq` / path already fully covered by tail turns if easy — optional; **must** never inject turn bodies that are not in hits or tail.
4. Fill code hits similarly under `code_rag_budget`.
5. If over `hard_cap`, drop lowest-score RAG messages first (never drop system; prefer keeping the latest tail turn).
6. `tokens_full_thread_est` = estimate of system + all turn texts concatenated.
7. `tokens_saved_est = max(0, full - assembled)`.

- [ ] **Step 1: Write failing tests**

```python
from mycelium.core.domain.chat_assembler import assemble_chat_prompt


def _turn(seq, role, text):
    return {"seq": seq, "role": role, "text": text, "token_est": max(1, len(text) // 4)}


def test_assembler_excludes_old_turns_not_in_hits():
    turns = [_turn(i, "user" if i % 2 else "assistant", f"turn-{i} " + ("x" * 40)) for i in range(1, 21)]
    hits = [{
        "id": "node:thread_chunk:t:5:0",
        "kind": "ThreadChunk",
        "path": "turn:5",
        "title": "turn-5",
        "snippet": "turn-5 relevant",
        "score": 0.9,
        "token_est": 10,
        "meta": {"turn_seq": 5},
    }]
    out = assemble_chat_prompt(
        system_text="You are Mycelium chat.",
        all_turns=turns,
        query_text="relevant",
        thread_hits=hits,
        code_hits=[],
        tail_k=2,
    )
    # Only seq 19,20 (tail) and hit referencing seq 5 content via snippet — not full turn 1..18 bodies
    assert 1 not in out["included_turn_seqs"]
    assert 19 in out["included_turn_seqs"] and 20 in out["included_turn_seqs"]
    blob = "\n".join(m["content"] for m in out["messages"])
    assert "turn-1 " not in blob
    assert out["tokens_assembled"] <= out["tokens_full_thread_est"]
    assert out["tokens_saved_est"] == out["tokens_full_thread_est"] - out["tokens_assembled"]


def test_assembler_respects_hard_cap():
    turns = [_turn(1, "user", "q"), _turn(2, "assistant", "a")]
    hits = [
        {"id": f"h{i}", "kind": "ThreadChunk", "path": "", "title": f"h{i}",
         "snippet": "y" * 800, "score": 1.0 - i * 0.01, "token_est": 200, "meta": {}}
        for i in range(20)
    ]
    out = assemble_chat_prompt(
        system_text="sys",
        all_turns=turns,
        query_text="q",
        thread_hits=hits,
        code_hits=[],
        hard_cap=500,
    )
    assert out["tokens_assembled"] <= 500
    assert out["truncated"] is True
```

- [ ] **Step 2: Run — expect FAIL**

```bash
cd services/core && python -m pytest tests/test_chat_assembler.py -v
```

- [ ] **Step 3: Implement `chat_assembler.py`** using `estimate_tokens` from `vault_service`.

- [ ] **Step 4: Run — expect PASS**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(core): add budgeted chat prompt assembler"
```

---

### Task 3: ThreadChunk in RAG + embed helper

**Files:**
- Modify: `services/core/src/mycelium/core/domain/node_types.py`
- Modify: `services/core/src/mycelium/core/domain/rag_service.py` (`_title_for`, `_snippet_for`, `display_kind_for_row`, add `query_thread`)
- Create: `services/core/src/mycelium/core/domain/thread_index.py` — upsert chunks into workspace vector store via existing embedding backend
- Test: `services/core/tests/test_thread_rag.py`

**Interfaces:**
- Produces:
  - `index_thread_chunks(embedding_service, workspace_id, chunks: list[dict]) -> int`
  - `RagService.query_thread(workspace_id, thread_id, query, limit=8) -> dict` (results filtered to `kind == ThreadChunk` and `meta.thread_id == thread_id`)

- [ ] **Step 1: Extend node types**

Add `"ThreadChunk"` to `FAMILIES` **or** map family to a new family `"Thread"` — prefer family `"Thread"` and display kind `"ThreadChunk"` so code demotion logic does not treat chunks as Notes.

Update `display_kind_for_row` to recognize `ThreadChunk` / `thread_chunk`.

- [ ] **Step 2: Failing test for query_thread filter**

```python
def test_query_thread_only_returns_matching_thread(tmp_path, monkeypatch):
    # Build minimal RagService with two ThreadChunk vectors in JsonVectorStore for ws
    # different thread_ids; query_thread must only return matching thread_id
    ...
```

Use hashing embedder / pre-written vectors like other core tests (see `tests/test_scaffold.py` patterns).

- [ ] **Step 3: Implement `query_thread` + indexing helper**

`index_thread_chunks`: for each chunk, call the same upsert path EmbeddingService uses for notes/files (prefer a thin public method on EmbeddingService if one exists; else duplicate the JsonVectorStore.upsert + embed call carefully).

- [ ] **Step 4: Tests PASS**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(core): index and retrieve ThreadChunk nodes"
```

---

### Task 4: ChatService + LLM port (echo)

**Files:**
- Create: `services/core/src/mycelium/core/ports/llm.py`
- Create: `services/core/src/mycelium/adapters/llm/echo.py`
- Create: `services/core/src/mycelium/adapters/llm/openai_compatible.py`
- Create: `services/core/src/mycelium/core/domain/chat_service.py`
- Modify: `services/core/src/mycelium/core/domain/impact_service.py` — add `record_chat_turn`
- Modify: `services/core/src/mycelium/core/config.py` — `[llm]` optional fields
- Test: `services/core/tests/test_chat_service.py`

**Interfaces:**

```python
# ports/llm.py
class LlmProvider(Protocol):
    def complete(self, messages: list[dict[str, str]], *, model: str | None = None) -> str: ...

# echo.py
class EchoLlm:
    def complete(self, messages, *, model=None) -> str:
        last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return f"echo: {last[:500]}"

# chat_service.py
class ChatService:
    def create_thread(self, *, workspace_id: str, title: str = "") -> dict: ...
    def list_threads(self, *, workspace_id: str | None = None) -> list[dict]: ...
    def get_thread(self, thread_id: str, *, offset: int = 0, limit: int = 100) -> dict: ...
    def search_thread(self, thread_id: str, query: str, *, limit: int = 8) -> dict: ...
    def send_message(
        self,
        thread_id: str,
        text: str,
        *,
        include_code_rag: bool = True,
        llm: LlmProvider | None = None,
    ) -> dict:
        """Returns {assistant, receipt, assembly, nudge_handoff: bool}"""
    def handoff(self, thread_id: str, *, summary: str | None = None) -> dict: ...
```

**`send_message` algorithm:**
1. Load thread; append user turn; `chunk_turn` + `index_thread_chunks` (best-effort; on embed failure set `index_stale`).
2. `system_text` = vault brain pack (`bucket="brain"`, `max_tokens=600`) if vault available, else short default string.
3. `thread_hits = rag.query_thread(...)` unless stale → `[]` + reason.
4. Optional `code_hits = rag.query(workspace_id, query=text, limit=6)` excluding ThreadChunk kinds.
5. `assembly = assemble_chat_prompt(...)`.
6. Resolve LLM: if none injected, require config key + `assert_allow_remote_llm`; else raise mapped errors.
7. `reply = llm.complete(assembly["messages"])`.
8. Append assistant turn; index chunks.
9. `mint_receipt(tool="chat", results=thread_hits+code_hits, served_tokens=assembly["tokens_assembled"])`.
10. `impact.record_chat_turn(served=..., baseline=assembly["tokens_full_thread_est"], ...)`.
11. `nudge_handoff = assembly["tokens_full_thread_est"] > 8000 or assembly["truncated"]`.
12. Return payload — **do not** include full `assembly["messages"]` in HTTP by default; include budgets + hit ids + optional `messages_preview` truncated for Context used UI (titles/snippets only).

**`handoff`:** Build markdown summary (last user intent + bullet of receipt ids/paths + open questions placeholder). `vault.create_note(title=..., body=..., bucket="work/active")`. Store `handoff_path` on thread. Body must not include full transcript.

- [ ] **Step 1: Failing tests**

```python
def test_send_message_with_echo_does_not_pass_full_thread(tmp_path):
    # seed 30 turns via store; send_message with EchoLlm
    # spy/wrap assembler or assert receipt served_tokens << full estimate
    # assert returned assembly tokens_saved_est > 0
    ...


def test_send_message_without_llm_key_errors(tmp_path):
    # ChatService with llm=None and empty config → error code llm_not_configured
    ...


def test_handoff_note_has_no_full_transcript(tmp_path):
    ...
```

- [ ] **Step 2–4: Implement + PASS**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(core): ChatService with RAG window and echo LLM"
```

---

### Task 5: HTTP `/threads` API

**Files:**
- Modify: `services/core/src/mycelium/adapters/http/app.py`
- Test: `services/core/tests/test_chat_http.py` (TestClient pattern from `test_scaffold.py` / `test_impact.py`)

**Routes:**

| Method | Path | Body / query | Behavior |
| --- | --- | --- | --- |
| POST | `/threads` | `{workspace_id, title?}` | create |
| GET | `/threads?workspace_id=` | | list |
| GET | `/threads/{id}?offset=&limit=` | | metadata + paginated turns |
| POST | `/threads/{id}/messages` | `{text, include_code_rag?}` | send_message |
| POST | `/threads/{id}/search` | `{query, limit?}` | search_thread |
| POST | `/threads/{id}/handoff` | `{summary?}` | handoff |

Wire `ChatService` in `create_app` beside other services. Map `PrivacyError` / domain errors to existing JSON error handler (`llm_not_configured`, `remote_llm_disabled`, `not_found`).

For LLM provider selection in app: if settings have key and `allow_remote_llm`, use `OpenAICompatibleLlm`; tests inject Echo via dependency override or `MYCELIUM_LLM=echo` env for integration tests.

- [ ] **Step 1: Write HTTP tests with Echo override**

```python
def test_messages_endpoint_returns_receipt(client):
    # create workspace fixture, POST /threads, POST messages
    body = resp.json()
    assert "receipt" in body
    assert body["assembly"]["tokens_assembled"] <= body["assembly"]["tokens_full_thread_est"]
```

- [ ] **Step 2–4: Implement routes + PASS**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(core): expose /threads chat HTTP API"
```

---

### Task 6: Desktop Chat UI + client

**Files:**
- Modify: `apps/desktop/src/api/client.ts`
- Create: `apps/desktop/src/pages/ChatPage.tsx`
- Modify: `apps/desktop/src/App.tsx`
- Modify: `apps/desktop/src/components/AppShell.tsx`
- Optional test: `apps/desktop/src/pages/ChatPage.layout.test.mjs` (mirror ImpactPage layout test style if present)

**Client additions:**

```typescript
export type ChatAssembly = {
  tokens_assembled: number;
  tokens_full_thread_est: number;
  tokens_saved_est: number;
  truncated: boolean;
  reason?: string | null;
  budgets: Record<string, number>;
  included_hit_ids: string[];
};

export type ChatMessageResponse = {
  assistant: { id: string; role: string; text: string; seq: number };
  receipt: { id: string; item_count: number; served_tokens: number; items?: ... };
  assembly: ChatAssembly;
  nudge_handoff?: boolean;
};

// createThread, listThreads, getThread, sendThreadMessage, searchThread, handoffThread
```

**ChatPage UX:**
- Left: thread list (create button; requires selected workspace — reuse Library/workspace selection pattern from SearchPage).
- Main: scrollable transcript (`getThread` pagination).
- Composer: textarea + Send → `sendThreadMessage`; disable when Core offline.
- Collapsible **Context used**: show `tokens_assembled` vs `tokens_full_thread_est`, hit titles/paths from receipt, truncated/reason badges.
- When `nudge_handoff`, show banner “Pin handoff to vault” → `handoffThread`.
- Copy: small honesty note in empty state — “Long threads stay in Mycelium Chat; Cursor’s own window is unchanged.”

**Nav:** insert `{ to: "/chat", label: "Chat", icon: "chat" }` before Impact or after Search.

- [ ] **Step 1: Add client functions + types**
- [ ] **Step 2: Add route + nav**
- [ ] **Step 3: Implement ChatPage**
- [ ] **Step 4: Manual smoke** — `pnpm --filter desktop dev` (or project’s usual script); create thread; send with Echo if remote LLM off
- [ ] **Step 5: Commit**

```bash
git commit -m "feat(desktop): add Mycelium Chat with Context used panel"
```

---

### Task 7: Settings LLM + Impact surface

**Files:**
- Modify: `apps/desktop/src/pages/SettingsPage.tsx`
- Modify: `services/core/src/mycelium/adapters/http/app.py` settings GET/PATCH if needed for `[llm]`
- Modify: `apps/desktop/src/pages/ImpactPage.tsx` — show chat-turn events (`tool === "chat"`) in existing list/summary if not automatic
- Modify: `CHANGELOG.md`
- Modify: `docs/superpowers/specs/2026-07-27-rag-conversation-window-design.md` status → Accepted
- Modify: `README.md` or `docs/AGENT-SECOND-BRAIN.md` — one short paragraph: Mycelium Chat RAG window; Cursor not rewritten

**Settings fields:**
- Toggle already exists mentally as `allow_remote_llm` — surface clearly for Chat.
- LLM base URL (default `https://api.openai.com/v1`), model id, API key (write to `~/.mycelium/llm_api_key` mode 0600 or OS keychain if already used elsewhere; **do not** commit keys). Prefer env var name `MYCELIUM_LLM_API_KEY` documented in UI.
- Optional budget overrides matching assembler defaults.

- [ ] **Step 1: Persist llm settings via existing patchSettings pattern**
- [ ] **Step 2: Impact shows chat savings**
- [ ] **Step 3: Docs + CHANGELOG**
- [ ] **Step 4: Commit**

```bash
git commit -m "feat: wire Chat LLM settings, Impact, and docs"
```

---

### Task 8 (optional / stretch): MCP `mycelium_thread_search`

**Files:**
- Modify: `services/core/src/mycelium/bridges/mcp/server.py`, `client.py`, `formatters.py`, rules docs

Only after Tasks 1–7. Tool searches a thread by id; packet compact + receipt. Instructions must say Cursor window is not compacted.

Skip in v1 ship if time-boxed — not required for the product guarantee.

---

## Self-review (plan vs spec)

| Spec requirement | Task |
| --- | --- |
| Mycelium-owned assemble loop | 4–5 |
| Tail + thread RAG + code RAG budgets | 2, 4 |
| Never full-thread prompt | 2 tests + 4 |
| Thread/Turn/Chunk model | 1, 3 |
| HTTP endpoints | 5 |
| Desktop Chat + Context used | 6 |
| Soft handoff nudge + vault note | 4, 6 |
| Opt-in LLM + privacy | 4, 7 |
| Impact tokens saved | 4, 7 |
| No Cursor fix claim | 6 empty state, 7 docs |
| Receipt attestation | 4 |
| index_stale behavior | 4 |
| MCP thin optional | 8 |

No TBD placeholders. Types aligned across tasks (`assembly` / `receipt` / `ThreadChunk` ids).

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-27-rag-conversation-window.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute tasks in this session with executing-plans checkpoints  

Which approach?
