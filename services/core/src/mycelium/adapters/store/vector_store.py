"""JSON vector store keyed by Node ID (LanceDB-compatible contract).

Chosen for zero-native-deps MVP; swap to LanceDB behind the same API later.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


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
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}

    def _write(self, data: dict[str, dict[str, Any]]) -> None:
        self._path.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def upsert(
        self,
        *,
        node_id: str,
        kind: str,
        text: str,
        vector: list[float],
        meta: dict[str, Any] | None = None,
    ) -> bool:
        """Upsert if content hash changed. Returns True if written."""
        data = self._read()
        digest = content_hash(text)
        existing = data.get(node_id)
        if existing and existing.get("content_hash") == digest:
            return False
        data[node_id] = {
            "node_id": node_id,
            "kind": kind,
            "text": text,
            "content_hash": digest,
            "vector": vector,
            "meta": meta or {},
        }
        self._write(data)
        return True

    def count(self) -> int:
        return len(self._read())

    def search(self, query_vector: list[float], *, limit: int = 10) -> list[dict[str, Any]]:
        rows = list(self._read().values())
        scored: list[tuple[float, dict[str, Any]]] = []
        for row in rows:
            score = cosine(query_vector, list(row.get("vector") or []))
            scored.append((score, row))
        scored.sort(key=lambda t: t[0], reverse=True)
        out: list[dict[str, Any]] = []
        for score, row in scored[: max(0, limit)]:
            out.append({**row, "score": score})
        return out

    def get(self, node_id: str) -> dict[str, Any] | None:
        return self._read().get(node_id)

    def all_rows(self) -> list[dict[str, Any]]:
        return list(self._read().values())
