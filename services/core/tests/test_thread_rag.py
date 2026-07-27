"""ThreadChunk RAG indexing + thread-scoped retrieval."""

from __future__ import annotations

from pathlib import Path

from mycelium.adapters.embeddings.bootstrap import EmbeddingStatus
from mycelium.adapters.embeddings.hashing import HashingEmbedder
from mycelium.adapters.store.json_io import atomic_write_json
from mycelium.adapters.store.vector_store import JsonVectorStore
from mycelium.adapters.store.workspace_repo import JsonFileWorkspaceRepo
from mycelium.core.domain.embedding_service import EmbeddingService
from mycelium.core.domain.node_types import display_kind_for_row, family_of
from mycelium.core.domain.rag_service import RagService
from mycelium.core.domain.thread_chunking import chunk_turn
from mycelium.core.domain.thread_index import index_thread_chunks


def _hashing_status() -> EmbeddingStatus:
    return EmbeddingStatus(
        model_id=HashingEmbedder.model_id,
        offline=True,
        cache_dir="",
        dimension=384,
        backend="hashing",
        notice="test",
    )


def _setup_workspace(tmp_path: Path) -> tuple[Path, str, JsonFileWorkspaceRepo]:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "workspaces").mkdir()
    ws_id = "ws-thread-rag"
    atomic_write_json(
        data_dir / "workspaces.json",
        [
            {
                "id": ws_id,
                "name": "thread-rag-test",
                "path": str(tmp_path / "repo"),
                "status": "idle",
            }
        ],
    )
    repo = JsonFileWorkspaceRepo(data_dir)
    return data_dir, ws_id, repo


def test_thread_chunk_node_type_family() -> None:
    assert family_of("ThreadChunk") == "Thread"
    assert (
        display_kind_for_row({"kind": "ThreadChunk", "meta": {"thread_id": "t"}})
        == "ThreadChunk"
    )
    assert (
        display_kind_for_row({"kind": "thread_chunk", "meta": {}}) == "ThreadChunk"
    )


def test_query_thread_only_returns_matching_thread(tmp_path: Path) -> None:
    data_dir, ws_id, repo = _setup_workspace(tmp_path)
    embedder = HashingEmbedder()
    status = _hashing_status()
    store = JsonVectorStore(data_dir / "workspaces" / ws_id)

    shared_body = "unique alpha topic about bananas and retrieval"
    for tid, suffix in (("thread:a", "a"), ("thread:b", "b")):
        text = f"{shared_body} marker-{suffix}"
        node_id = f"node:thread_chunk:{tid}:1:0"
        store.upsert(
            node_id=node_id,
            kind="ThreadChunk",
            text=text,
            vector=embedder.embed([text])[0],
            model_id=HashingEmbedder.model_id,
            meta={
                "thread_id": tid,
                "turn_seq": 1,
                "role": "user",
                "chunk_i": 0,
                "kind": "ThreadChunk",
                "family": "Thread",
            },
        )

    rag = RagService(
        data_dir=data_dir,
        runtime=embedder,
        status=status,
        workspace_repo=repo,
    )
    result = rag.query_thread(
        workspace_id=ws_id,
        thread_id="thread:a",
        query="bananas retrieval",
        limit=8,
    )
    assert result["count"] >= 1
    assert result["thread_id"] == "thread:a"
    assert all(
        (r.get("thread_id") == "thread:a")
        or ("thread:a" in str(r.get("id") or ""))
        for r in result["results"]
    )
    assert not any("thread:b" in str(r.get("id") or "") for r in result["results"])
    for row in result["results"]:
        assert row["kind"] == "ThreadChunk"
        assert row["family"] == "Thread"


def test_index_thread_chunks_upserts_vectors(tmp_path: Path) -> None:
    data_dir, ws_id, repo = _setup_workspace(tmp_path)
    embedder = HashingEmbedder()
    status = _hashing_status()
    emb = EmbeddingService(
        data_dir=data_dir,
        runtime=embedder,
        status=status,
        workspace_repo=repo,
    )
    chunks = chunk_turn(
        thread_id="thread:x",
        seq=1,
        role="user",
        text="hello world about widgets and mycelium",
    )
    written = index_thread_chunks(emb, ws_id, chunks)
    assert written >= 1
    store = JsonVectorStore(data_dir / "workspaces" / ws_id)
    row = store.get(chunks[0]["id"])
    assert row is not None
    assert row["kind"] == "ThreadChunk"
    assert row["meta"]["thread_id"] == "thread:x"

    rag = RagService(
        data_dir=data_dir,
        runtime=embedder,
        status=status,
        workspace_repo=repo,
    )
    hit = rag.query_thread(
        workspace_id=ws_id,
        thread_id="thread:x",
        query="widgets mycelium",
        limit=4,
    )
    assert hit["count"] >= 1
    assert hit["results"][0]["id"] == chunks[0]["id"]


def test_query_default_excludes_thread_chunks(tmp_path: Path) -> None:
    """Desktop Search / MCP query must not leak ThreadChunk without kinds opt-in."""
    data_dir, ws_id, repo = _setup_workspace(tmp_path)
    embedder = HashingEmbedder()
    status = _hashing_status()
    store = JsonVectorStore(data_dir / "workspaces" / ws_id)

    marker = "THREAD_LEAK_BANANA_WIDGET_XYZ"
    thread_text = f"conversation about {marker}"
    code_text = f"def widget(): return '{marker}'"
    store.upsert(
        node_id="node:thread_chunk:thread:leak:1:0",
        kind="ThreadChunk",
        text=thread_text,
        vector=embedder.embed([thread_text])[0],
        model_id=HashingEmbedder.model_id,
        meta={
            "thread_id": "thread:leak",
            "turn_seq": 1,
            "role": "user",
            "kind": "ThreadChunk",
            "family": "Thread",
        },
    )
    store.upsert(
        node_id="node:symbol:demo:widget",
        kind="Function",
        text=code_text,
        vector=embedder.embed([code_text])[0],
        model_id=HashingEmbedder.model_id,
        meta={"name": "widget", "path": "demo.py", "symbol_kind": "function"},
    )

    rag = RagService(
        data_dir=data_dir,
        runtime=embedder,
        status=status,
        workspace_repo=repo,
    )
    default = rag.query(workspace_id=ws_id, query=marker, limit=8)
    kinds = {r["kind"] for r in default["results"]}
    assert "ThreadChunk" not in kinds
    assert not any(
        str(r.get("id") or "").startswith("node:thread_chunk:")
        for r in default["results"]
    )

    opted = rag.query(
        workspace_id=ws_id,
        query=marker,
        limit=8,
        kinds=["ThreadChunk"],
    )
    assert any(r["kind"] == "ThreadChunk" for r in opted["results"])
    assert any(
        str(r.get("id") or "").startswith("node:thread_chunk:")
        for r in opted["results"]
    )
