"""JSON Edge store — co_changed and other graph links."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonEdgeStore:
    def __init__(self, workspace_dir: Path) -> None:
        self._dir = workspace_dir
        self._path = workspace_dir / "edges.json"
        self._dir.mkdir(parents=True, exist_ok=True)
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

    def replace_snapshot(self, edges: list[dict[str, Any]]) -> int:
        data = {e["id"]: e for e in edges}
        self._write(data)
        return len(data)

    def list_edges(self, *, kind: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return self.list_all(kind=kind)[: max(0, limit)]

    def list_all(self, *, kind: str | None = None) -> list[dict[str, Any]]:
        rows = list(self._read().values())
        if kind:
            rows = [r for r in rows if r.get("edge_kind") == kind]
        rows.sort(key=lambda r: r.get("id", ""))
        return rows

    def count(self, *, kind: str | None = None) -> int:
        rows = self._read().values()
        if kind:
            return sum(1 for r in rows if r.get("edge_kind") == kind)
        return len(self._read())
