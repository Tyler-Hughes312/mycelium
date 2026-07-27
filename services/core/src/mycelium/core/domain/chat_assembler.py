"""Budgeted chat prompt assembly — never concatenates the full thread."""

from __future__ import annotations

from typing import Any

from mycelium.core.domain.vault_service import estimate_tokens

_SYSTEM_TOKEN_CAP = 600


def _hit_tokens(hit: dict[str, Any]) -> int:
    if hit.get("token_est") is not None:
        return max(0, int(hit["token_est"]))
    return estimate_tokens(str(hit.get("snippet") or ""))


def _turn_tokens(turn: dict[str, Any]) -> int:
    if turn.get("token_est") is not None:
        return max(0, int(turn["token_est"]))
    return estimate_tokens(str(turn.get("text") or ""))


def _truncate_to_tokens(text: str, max_tokens: int) -> tuple[str, bool]:
    """Truncate text so estimate_tokens(result) <= max_tokens."""
    if max_tokens <= 0:
        return "", bool(text)
    if estimate_tokens(text) <= max_tokens:
        return text, False
    # estimate_tokens = max(1, len // 4) for non-empty → max_chars = max_tokens * 4
    max_chars = max_tokens * 4
    truncated = text[:max_chars]
    # Ensure we actually fit (empty → 0 tokens)
    while truncated and estimate_tokens(truncated) > max_tokens:
        truncated = truncated[:-1]
    return truncated, True


def _messages_tokens(messages: list[dict[str, str]]) -> int:
    return sum(estimate_tokens(m.get("content") or "") for m in messages)


def _format_hit_content(hit: dict[str, Any]) -> str:
    snippet = str(hit.get("snippet") or "")
    return snippet


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
) -> dict:
    """Assemble OpenAI-style messages from system + recent tail + RAG hits only.

    Invariant: assembled prompt ⊆ system prefs ∪ recent tail ∪ RAG hits —
    never concatenates the full thread. ``query_text`` is accepted for the
    caller's retrieval context; the new user turn is expected in ``all_turns``.
    """
    _ = query_text  # retrieval query; turn body lives in all_turns / tail
    truncated = False
    reason: str | None = None

    system_content, sys_trunc = _truncate_to_tokens(system_text or "", _SYSTEM_TOKEN_CAP)
    if sys_trunc:
        truncated = True

    turns_sorted = sorted(all_turns or [], key=lambda t: int(t.get("seq", 0)))

    # --- Tail: last tail_k by seq, drop oldest until under budget ---
    tail: list[dict[str, Any]] = list(turns_sorted[-tail_k:]) if tail_k > 0 else []
    while len(tail) > 1 and sum(_turn_tokens(t) for t in tail) > tail_token_budget:
        tail.pop(0)
        truncated = True
    if tail and sum(_turn_tokens(t) for t in tail) > tail_token_budget:
        # Single remaining turn still over budget — truncate its text in place copy
        only = dict(tail[0])
        text = str(only.get("text") or "")
        trimmed, was_trunc = _truncate_to_tokens(text, tail_token_budget)
        only["text"] = trimmed
        only["token_est"] = estimate_tokens(trimmed)
        tail = [only]
        if was_trunc:
            truncated = True

    tail_seqs = {int(t["seq"]) for t in tail if t.get("seq") is not None}

    def _select_hits(
        hits: list[dict],
        budget: int,
        *,
        skip_tail_covered: bool,
    ) -> list[dict[str, Any]]:
        nonlocal truncated
        selected: list[dict[str, Any]] = []
        used = 0
        ordered = sorted(hits or [], key=lambda h: float(h.get("score") or 0.0), reverse=True)
        for hit in ordered:
            meta = hit.get("meta") or {}
            turn_seq = meta.get("turn_seq")
            if skip_tail_covered and turn_seq is not None and int(turn_seq) in tail_seqs:
                continue
            cost = _hit_tokens(hit)
            if cost <= 0 and not (hit.get("snippet") or ""):
                continue
            if used + cost > budget:
                truncated = True
                continue
            selected.append(hit)
            used += cost
        return selected

    thread_selected = _select_hits(thread_hits, thread_rag_budget, skip_tail_covered=True)
    code_selected = _select_hits(code_hits, code_rag_budget, skip_tail_covered=False)

    # Track RAG slots for hard-cap eviction (lowest score first)
    rag_slots: list[dict[str, Any]] = []
    for hit in thread_selected:
        rag_slots.append(
            {
                "id": str(hit.get("id") or ""),
                "score": float(hit.get("score") or 0.0),
                "content": _format_hit_content(hit),
                "scope": "thread",
            }
        )
    for hit in code_selected:
        rag_slots.append(
            {
                "id": str(hit.get("id") or ""),
                "score": float(hit.get("score") or 0.0),
                "content": _format_hit_content(hit),
                "scope": "code",
            }
        )

    def _build_messages(
        system: str,
        slots: list[dict[str, Any]],
        tail_turns: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        msgs: list[dict[str, str]] = [{"role": "system", "content": system}]
        for slot in slots:
            msgs.append({"role": "system", "content": slot["content"]})
        for turn in tail_turns:
            role = str(turn.get("role") or "user")
            msgs.append({"role": role, "content": str(turn.get("text") or "")})
        return msgs

    messages = _build_messages(system_content, rag_slots, tail)

    # --- Hard cap: drop lowest-score RAG first; never drop system; keep latest tail ---
    while _messages_tokens(messages) > hard_cap and rag_slots:
        lowest_i = min(range(len(rag_slots)), key=lambda i: (rag_slots[i]["score"], i))
        rag_slots.pop(lowest_i)
        messages = _build_messages(system_content, rag_slots, tail)
        truncated = True

    while _messages_tokens(messages) > hard_cap and len(tail) > 1:
        tail.pop(0)
        tail_seqs = {int(t["seq"]) for t in tail if t.get("seq") is not None}
        messages = _build_messages(system_content, rag_slots, tail)
        truncated = True

    if _messages_tokens(messages) > hard_cap and tail:
        # Truncate the latest (only) tail turn to fit remaining budget
        reserved = _messages_tokens([{"role": "system", "content": system_content}])
        reserved += sum(estimate_tokens(s["content"]) for s in rag_slots)
        remaining = max(0, hard_cap - reserved)
        only = dict(tail[-1])
        trimmed, was_trunc = _truncate_to_tokens(str(only.get("text") or ""), remaining)
        only["text"] = trimmed
        only["token_est"] = estimate_tokens(trimmed)
        tail = [only]
        tail_seqs = {int(t["seq"]) for t in tail if t.get("seq") is not None}
        messages = _build_messages(system_content, rag_slots, tail)
        if was_trunc:
            truncated = True

    if _messages_tokens(messages) > hard_cap:
        # Last resort: shrink system (still present) to fit hard_cap alone
        trimmed, was_trunc = _truncate_to_tokens(system_content, hard_cap)
        system_content = trimmed
        rag_slots = []
        tail = []
        tail_seqs = set()
        messages = _build_messages(system_content, rag_slots, tail)
        if was_trunc:
            truncated = True

    tokens_assembled = _messages_tokens(messages)
    # Clamp reporting if estimate still slightly over (should not happen)
    if tokens_assembled > hard_cap:
        truncated = True

    full_blob = (system_text or "") + "".join(str(t.get("text") or "") for t in turns_sorted)
    tokens_full_thread_est = estimate_tokens(full_blob) if full_blob else 0
    tokens_saved_est = max(0, tokens_full_thread_est - tokens_assembled)

    included_hit_ids = [s["id"] for s in rag_slots if s.get("id")]

    return {
        "messages": messages,
        "included_turn_seqs": set(tail_seqs),
        "included_hit_ids": included_hit_ids,
        "tokens_assembled": tokens_assembled,
        "tokens_full_thread_est": tokens_full_thread_est,
        "tokens_saved_est": tokens_saved_est,
        "budgets": {
            "tail_k": tail_k,
            "tail_token_budget": tail_token_budget,
            "thread_rag_budget": thread_rag_budget,
            "code_rag_budget": code_rag_budget,
            "hard_cap": hard_cap,
            "system_token_cap": _SYSTEM_TOKEN_CAP,
        },
        "truncated": truncated,
        "reason": reason,
    }
