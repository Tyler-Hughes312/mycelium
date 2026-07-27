# MemoryOptimization

## Mycelium context layer (required)

This repo runs a local Mycelium Core (`http://127.0.0.1:8787`) that provides RAG-scoped,
token-budgeted context — the same chunk/embed/retrieve/budget-assemble pipeline used by
`services/core/src/mycelium/core/domain/chat_assembler.py` and `rag_service.py`, but applied
to the coding session itself instead of the chat product. Use it instead of broad grepping
or dumping whole files.

- At the start of meaningful work, call `mycelium_session_start` (or `mycelium_preflight` for
  lighter exploration) with the absolute workspace path. It returns a compact bootstrap packet
  plus a one-line receipt — cite the receipt, don't re-fetch the full vault/code.
- Before planning or building anything new, call `mycelium_reuse_check(goal)` first — it checks
  for prior art across all indexed repos. If it says to ask the user reuse-vs-new, ask and wait.
- Prefer `mycelium_change_context(goal)` when implementing, `mycelium_debug_context(error)` when
  fixing, and `mycelium_search(query)` for general lookups — over grepping or globbing many files.
- Do not dump chat transcripts into the vault, and do not paste full files when a receipt already
  covers the hit list.

If `mycelium_health` reports the Core is unreachable, fall back to normal exploration (Explore
agent / grep) rather than blocking on it.
