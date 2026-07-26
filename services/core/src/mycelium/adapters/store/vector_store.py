"""JSON vector store keyed by Node ID (LanceDB-compatible contract).

Chosen for zero-native-deps MVP; swap to LanceDB behind the same API later.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

from mycelium.adapters.store.json_io import atomic_write_json, file_lock, read_json_object


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


class JsonVectorStore:
    def __init__(self, workspace_dir: Path) -> None:
        self._path = workspace_dir / "vectors.json"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write({})

    def _read(self) -> dict[str, dict[str, Any]]:
        raw = read_json_object(self._path, default={})
        return raw if isinstance(raw, dict) else {}

    def _write(self, data: dict[str, dict[str, Any]]) -> None:
        atomic_write_json(self._path, data)

    def upsert(
        self,
        *,
        node_id: str,
        kind: str,
        text: str,
        vector: list[float],
        model_id: str,
        meta: dict[str, Any] | None = None,
    ) -> bool:
        """Upsert if content hash or model changed. Returns True if written."""
        with file_lock(self._path):
            data = self._read()
            digest = content_hash(text)
            existing = data.get(node_id)
            if (
                existing
                and existing.get("content_hash") == digest
                and existing.get("model_id") == model_id
                and len(existing.get("vector") or []) == len(vector)
            ):
                return False
            data[node_id] = {
                "node_id": node_id,
                "kind": kind,
                "text": text,
                "content_hash": digest,
                "model_id": model_id,
                "vector": vector,
                "meta": meta or {},
            }
            self._write(data)
            return True

    def upsert_many(
        self,
        rows: list[dict[str, Any]],
    ) -> tuple[int, int]:
        """
        Batch upsert under one lock / one atomic write.

        Each row: node_id, kind, text, vector, model_id, meta?
        Returns (written, skipped_unchanged).
        """
        if not rows:
            return 0, 0
        written = 0
        skipped = 0
        with file_lock(self._path):
            data = self._read()
            for row in rows:
                node_id = str(row["node_id"])
                text = str(row["text"])
                model_id = str(row["model_id"])
                vector = list(row["vector"])
                digest = content_hash(text)
                existing = data.get(node_id)
                if (
                    existing
                    and existing.get("content_hash") == digest
                    and existing.get("model_id") == model_id
                    and len(existing.get("vector") or []) == len(vector)
                ):
                    skipped += 1
                    continue
                data[node_id] = {
                    "node_id": node_id,
                    "kind": row.get("kind") or "Unknown",
                    "text": text,
                    "content_hash": digest,
                    "model_id": model_id,
                    "vector": vector,
                    "meta": row.get("meta") or {},
                }
                written += 1
            if written:
                self._write(data)
        return written, skipped

    def count(self) -> int:
        return len(self._read())

    def search(self, query_vector: list[float], *, limit: int = 10) -> list[dict[str, Any]]:
        rows = list(self._read().values())
        scored: list[tuple[float, dict[str, Any]]] = []
        for row in rows:
            vec = list(row.get("vector") or [])
            if len(vec) != len(query_vector):
                continue
            score = cosine(query_vector, vec)
            scored.append((score, row))
        scored.sort(key=lambda t: t[0], reverse=True)
        out: list[dict[str, Any]] = []
        for score, row in scored[: max(0, limit)]:
            out.append({**row, "score": score})
        return out

    def get(self, node_id: str) -> dict[str, Any] | None:
        return self._read().get(node_id)

    def delete(self, node_id: str) -> bool:
        with file_lock(self._path):
            data = self._read()
            if node_id not in data:
                return False
            del data[node_id]
            self._write(data)
            return True

    def replace_all(self, data: dict[str, dict[str, Any]]) -> None:
        with file_lock(self._path):
            self._write(data)

    def all_rows(self) -> list[dict[str, Any]]:
        return list(self._read().values())
