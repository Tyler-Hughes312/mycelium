"""ChatService — RAG window assembly + echo LLM (never full thread)."""

from __future__ import annotations

from pathlib import Path

import pytest

from mycelium.adapters.embeddings.bootstrap import EmbeddingStatus
from mycelium.adapters.embeddings.hashing import HashingEmbedder
from mycelium.adapters.llm.echo import EchoLlm
from mycelium.adapters.store.impact_store import ImpactStore
from mycelium.adapters.store.json_io import atomic_write_json
from mycelium.adapters.store.thread_store import ThreadStore
from mycelium.adapters.store.workspace_repo import JsonFileWorkspaceRepo
from mycelium.core.config import ensure_local_layout
from mycelium.core.domain.chat_service import ChatError, ChatService
from mycelium.core.domain.context_receipt import ReceiptStore
from mycelium.core.domain.embedding_service import EmbeddingService
from mycelium.core.domain.impact_service import ImpactService
from mycelium.core.domain.rag_service import RagService
from mycelium.core.domain.vault_service import VaultService


def _hashing_status() -> EmbeddingStatus:
    return EmbeddingStatus(
        model_id=HashingEmbedder.model_id,
        offline=True,
        cache_dir="",
        dimension=384,
        backend="hashing",
        notice="test",
    )


def _build_chat(tmp_path: Path) -> tuple[ChatService, ThreadStore, str, Path]:
    home = tmp_path / "home"
    cfg = ensure_local_layout(home)
    data_dir = cfg.paths.data_dir
    (data_dir / "workspaces").mkdir(parents=True, exist_ok=True)
    ws_id = "ws-chat"
    atomic_write_json(
        data_dir / "workspaces.json",
        [
            {
                "id": ws_id,
                "name": "chat-test",
                "path": str(tmp_path / "repo"),
                "status": "idle",
            }
        ],
    )
    repo = JsonFileWorkspaceRepo(data_dir)
    embedder = HashingEmbedder()
    status = _hashing_status()
    emb = EmbeddingService(
        data_dir=data_dir,
        runtime=embedder,
        status=status,
        workspace_repo=repo,
    )
    rag = RagService(
        data_dir=data_dir,
        runtime=embedder,
        status=status,
        workspace_repo=repo,
    )
    vault = VaultService(
        vault_dir=cfg.paths.vault_dir,
        data_dir=data_dir,
        workspace_repo=repo,
        runtime=embedder,
        status=status,
    )
    impact = ImpactService(ImpactStore(data_dir / "impact_events.json"))
    receipts = ReceiptStore(data_dir / "receipts.json")
    threads = ThreadStore(data_dir / "threads")
    chat = ChatService(
        threads=threads,
        rag=rag,
        embedding=emb,
        vault=vault,
        impact=impact,
        receipts=receipts,
        config=cfg,
    )
    return chat, threads, ws_id, home


def test_send_message_with_echo_does_not_pass_full_thread(tmp_path: Path) -> None:
    chat, threads, ws_id, _home = _build_chat(tmp_path)
    t = threads.create(workspace_id=ws_id, title="long")
    # Seed many prior turns so full-thread estimate dwarfs assembled window.
    for i in range(30):
        threads.append_turn(
            t["id"],
            role="user" if i % 2 == 0 else "assistant",
            text=f"prior turn {i} " + ("filler words " * 40),
        )

    spy_messages: list[list[dict[str, str]]] = []

    class SpyEcho(EchoLlm):
        def complete(self, messages, *, model=None) -> str:  # type: ignore[no-untyped-def]
            spy_messages.append(list(messages))
            return super().complete(messages, model=model)

    out = chat.send_message(t["id"], "what about bananas?", llm=SpyEcho())
    assert "assistant" in out
    assert out["assistant"]["role"] == "assistant"
    assert out["assistant"]["text"].startswith("echo:")
    assembly = out["assembly"]
    assert assembly["tokens_saved_est"] > 0
    assert assembly["tokens_assembled"] < assembly["tokens_full_thread_est"]
    assert out["receipt"]["served_tokens"] == assembly["tokens_assembled"]
    assert out["receipt"]["served_tokens"] < assembly["tokens_full_thread_est"] // 2
    # Payload must not dump full OpenAI messages by default
    assert "messages" not in assembly or assembly.get("messages") is None
    assert "messages_preview" in assembly
    assert spy_messages, "LLM should have been called"
    # Assembled prompt is small: no prior filler dump of all 30 turns
    blob = " ".join(m["content"] for m in spy_messages[0])
    assert blob.count("prior turn") <= 3
    # One tail turn may include ~40 fillers; full thread would be ~600+
    assert blob.count("filler words") < 120


def test_send_message_without_llm_key_errors(tmp_path: Path) -> None:
    chat, threads, ws_id, _home = _build_chat(tmp_path)
    t = threads.create(workspace_id=ws_id, title="no-key")
    with pytest.raises(ChatError) as ei:
        chat.send_message(t["id"], "hello", llm=None)
    assert ei.value.code == "llm_not_configured"


def test_llm_not_configured_leaves_turn_count_unchanged(tmp_path: Path) -> None:
    """Missing LLM must fail before append_turn — no orphaned user message."""
    chat, threads, ws_id, _home = _build_chat(tmp_path)
    t = threads.create(workspace_id=ws_id, title="no-orphan")
    before = chat.get_thread(t["id"])["turn_count"]
    with pytest.raises(ChatError) as ei:
        chat.send_message(t["id"], "hello without key", llm=None)
    assert ei.value.code == "llm_not_configured"
    after = chat.get_thread(t["id"])["turn_count"]
    assert after == before
    turns = threads.list_turns(t["id"])
    assert turns == []


def test_thread_chunk_excluded_from_code_hits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Thread family rows must not enter code_hits even if kind is lowercase/meta-only."""
    chat, threads, ws_id, _home = _build_chat(tmp_path)
    t = threads.create(workspace_id=ws_id, title="code-filter")
    marker = "THREAD_CHUNK_MUST_NOT_REACH_CODE_RAG_XYZ"

    def fake_code_query(
        self: RagService,  # noqa: ARG001
        *,
        workspace_id: str,  # noqa: ARG001
        query: str,  # noqa: ARG001
        limit: int = 8,  # noqa: ARG001
        **_kwargs: object,
    ) -> dict:
        return {
            "results": [
                {
                    "id": f"node:thread_chunk:{t['id']}:1:0",
                    # lowercase + meta — old `kind == "ThreadChunk"` filter missed this
                    "kind": "thread_chunk",
                    "path": "",
                    "title": "leaked chunk",
                    "snippet": marker,
                    "meta": {"kind": "thread_chunk", "thread_id": t["id"], "turn_seq": 1},
                },
                {
                    "id": "node:symbol:demo:foo",
                    "kind": "Function",
                    "path": "demo.py",
                    "title": "foo",
                    "snippet": "def foo(): return 1",
                    "meta": {"symbol_kind": "function"},
                },
            ]
        }

    monkeypatch.setattr(RagService, "query", fake_code_query)

    spy_messages: list[list[dict[str, str]]] = []

    class SpyEcho(EchoLlm):
        def complete(self, messages, *, model=None) -> str:  # type: ignore[no-untyped-def]
            spy_messages.append(list(messages))
            return super().complete(messages, model=model)

    out = chat.send_message(t["id"], "find foo", llm=SpyEcho(), include_code_rag=True)
    assert spy_messages
    blob = " ".join(m["content"] for m in spy_messages[0])
    assert marker not in blob
    included = set(out["assembly"].get("included_hit_ids") or [])
    assert f"node:thread_chunk:{t['id']}:1:0" not in included
    # Legitimate code hit may still assemble
    assert "def foo" in blob or "node:symbol:demo:foo" in included or "foo" in blob


def test_index_stale_falls_back_to_tail_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Embed/index failure → reason=index_stale, no thread hits, prompt still bounded."""
    chat, threads, ws_id, _home = _build_chat(tmp_path)
    t = threads.create(workspace_id=ws_id, title="stale-index")
    for i in range(30):
        threads.append_turn(
            t["id"],
            role="user" if i % 2 == 0 else "assistant",
            text=f"prior turn {i} " + ("filler words " * 40),
        )

    def boom(*_args: object, **_kwargs: object) -> int:
        raise RuntimeError("forced embed failure")

    monkeypatch.setattr(
        "mycelium.core.domain.chat_service.index_thread_chunks",
        boom,
    )

    spy_messages: list[list[dict[str, str]]] = []

    class SpyEcho(EchoLlm):
        def complete(self, messages, *, model=None) -> str:  # type: ignore[no-untyped-def]
            spy_messages.append(list(messages))
            return super().complete(messages, model=model)

    out = chat.send_message(
        t["id"],
        "what about bananas?",
        llm=SpyEcho(),
        include_code_rag=False,
    )
    assembly = out["assembly"]
    assert assembly["reason"] == "index_stale"
    assert assembly.get("included_hit_ids") in ([], None) or not any(
        str(hid).startswith("node:thread_chunk:")
        for hid in (assembly.get("included_hit_ids") or [])
    )
    assert assembly["tokens_assembled"] < assembly["tokens_full_thread_est"]
    assert spy_messages
    blob = " ".join(m["content"] for m in spy_messages[0])
    # Tail-only path: must not dump all 30 prior turns
    assert blob.count("prior turn") <= 3
    assert blob.count("filler words") < 120


def test_llm_upstream_failure_appends_error_turn(tmp_path: Path) -> None:
    """complete() failure → ChatError(llm_upstream) + short assistant error turn."""
    chat, threads, ws_id, _home = _build_chat(tmp_path)
    t = threads.create(workspace_id=ws_id, title="upstream-fail")

    class BoomLlm:
        def complete(self, messages, *, model=None) -> str:  # type: ignore[no-untyped-def]
            raise RuntimeError("connection reset by peer")

    with pytest.raises(ChatError) as ei:
        chat.send_message(t["id"], "hello upstream", llm=BoomLlm())
    assert ei.value.code == "llm_upstream"
    turns = threads.list_turns(t["id"])
    assert len(turns) == 2
    assert turns[0]["role"] == "user"
    assert turns[0]["text"] == "hello upstream"
    assert turns[1]["role"] == "assistant"
    assert "failed" in turns[1]["text"].lower()


def test_handoff_note_has_no_full_transcript(tmp_path: Path) -> None:
    chat, threads, ws_id, home = _build_chat(tmp_path)
    t = threads.create(workspace_id=ws_id, title="handoff-demo")
    secret = "UNIQUE_TRANSCRIPT_SECRET_PHRASE_XYZ_999"
    threads.append_turn(t["id"], role="user", text=f"Please help with {secret}")
    threads.append_turn(t["id"], role="assistant", text=f"Sure about {secret}")
    # Produce a receipt so handoff can cite it
    chat.send_message(t["id"], "follow up without secret", llm=EchoLlm())

    result = chat.handoff(t["id"], summary="Pin current intent")
    assert "note" in result or "path" in result or "handoff_path" in result
    handoff_path = result.get("handoff_path") or result.get("path") or ""
    assert handoff_path
    body = (result.get("note") or {}).get("body") or ""
    if not body:
        # Fall back to reading vault note file
        note_path = home / "vault" / handoff_path
        if not note_path.is_file():
            note_path = Path(result.get("note", {}).get("abs_path") or "")
        assert note_path.is_file()
        body = note_path.read_text(encoding="utf-8")
    assert secret not in body
    assert "UNIQUE_TRANSCRIPT" not in body
    # Curated structure
    assert "Open questions" in body or "open questions" in body.lower()
