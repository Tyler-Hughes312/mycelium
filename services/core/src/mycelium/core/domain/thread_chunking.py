"""Split thread turns into embeddable chunks for RAG retrieval."""

from __future__ import annotations

from typing import Any


def chunk_turn(
    *,
    thread_id: str,
    seq: int,
    role: str,
    text: str,
    max_chars: int = 800,
) -> list[dict[str, Any]]:
    """Split turn text on whitespace into <= max_chars pieces."""
    if not text:
        return []

    words = text.split()
    if not words:
        return []

    pieces: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        extra = len(word) if not current else len(word) + 1
        if current and current_len + extra > max_chars:
            pieces.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += extra

    if current:
        pieces.append(" ".join(current))

    chunks: list[dict[str, Any]] = []
    for i, piece in enumerate(pieces):
        if not piece:
            continue
        chunks.append(
            {
                "id": f"node:thread_chunk:{thread_id}:{seq}:{i}",
                "kind": "ThreadChunk",
                "text": piece,
                "meta": {
                    "thread_id": thread_id,
                    "turn_seq": seq,
                    "role": role,
                    "chunk_i": i,
                },
            }
        )
    return chunks
