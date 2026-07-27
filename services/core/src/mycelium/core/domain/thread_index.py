"""Index ThreadChunk nodes into the workspace vector store."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mycelium.core.domain.node_types import embed_type_prefix

if TYPE_CHECKING:
    from mycelium.core.domain.embedding_service import EmbeddingService


def thread_chunk_embed_text(chunk: dict[str, Any]) -> str:
    meta = dict(chunk.get("meta") or {})
    body = str(chunk.get("text") or "")
    parts = [
        embed_type_prefix("ThreadChunk"),
        f"thread: {meta['thread_id']}" if meta.get("thread_id") else "",
        f"role: {meta['role']}" if meta.get("role") else "",
        f"turn: {meta['turn_seq']}" if meta.get("turn_seq") is not None else "",
        "body:",
        body,
    ]
    return "\n".join(p for p in parts if p)


def index_thread_chunks(
    embedding_service: EmbeddingService,
    workspace_id: str,
    chunks: list[dict[str, Any]],
) -> int:
    """Upsert ThreadChunk embeddings. Returns number of vectors written."""
    if not chunks:
        return 0
    nodes: list[dict[str, Any]] = []
    for chunk in chunks:
        node_id = str(chunk.get("id") or chunk.get("node_id") or "")
        if not node_id:
            continue
        meta = dict(chunk.get("meta") or {})
        meta.setdefault("kind", "ThreadChunk")
        meta.setdefault("family", "Thread")
        nodes.append(
            {
                "node_id": node_id,
                "kind": "ThreadChunk",
                "text": thread_chunk_embed_text(chunk),
                "meta": meta,
            }
        )
    written, _skipped = embedding_service.upsert_nodes(workspace_id, nodes)
    return written
