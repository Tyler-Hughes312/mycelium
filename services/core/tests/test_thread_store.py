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
