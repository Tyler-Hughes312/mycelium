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


def test_assembler_rejects_understated_token_est_for_packing():
    """Understated token_est must not let huge snippets slip under a tiny budget."""
    huge = "x" * 800  # ~200 tokens via estimate_tokens
    hits = [
        {
            "id": "h-under",
            "kind": "ThreadChunk",
            "path": "",
            "title": "h-under",
            "snippet": huge,
            "score": 1.0,
            "token_est": 0,
            "meta": {},
        },
    ]
    out = assemble_chat_prompt(
        system_text="sys",
        all_turns=[],
        query_text="q",
        thread_hits=hits,
        code_hits=[],
        thread_rag_budget=50,
    )
    assert "h-under" not in out["included_hit_ids"]
    assert out["truncated"] is True
