"""JSON Edge store — co_changed and other graph links."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mycelium.adapters.store.json_io import atomic_write_json, read_json_object


class JsonEdgeStore:
    def __init__(self, workspace_dir: Path) -> None:
        self._dir = workspace_dir
        self._path = workspace_dir / "edges.json"
        self._dir.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write({})

    def _read(self) -> dict[str, dict[str, Any]]:
        raw = read_json_object(self._path, default={})
        return raw if isinstance(raw, dict) else {}

    def _write(self, data: dict[str, dict[str, Any]]) -> None:
        atomic_write_json(self._path, data)

    def replace_snapshot(self, edges: list[dict[str, Any]]) -> int:
        data = {e["id"]: e for e in edges}
        self._write(data)
        return len(data)

    def replace_kinds(self, *, kinds: set[str], edges: list[dict[str, Any]]) -> int:
        """Replace only edges whose edge_kind is in `kinds`; keep others."""
        data = {
            eid: row
            for eid, row in self._read().items()
            if row.get("edge_kind") not in kinds
        }
        for edge in edges:
            data[edge["id"]] = edge
        self._write(data)
        return len(data)

    def upsert_edges(self, edges: list[dict[str, Any]]) -> int:
        data = self._read()
        for edge in edges:
            data[edge["id"]] = edge
        self._write(data)
        return len(data)

    def delete_by_source(self, source_id: str, *, kinds: set[str] | None = None) -> int:
        data = self._read()
        keep: dict[str, dict[str, Any]] = {}
        removed = 0
        for eid, row in data.items():
            if row.get("source_id") == source_id and (
                kinds is None or row.get("edge_kind") in kinds
            ):
                removed += 1
                continue
            keep[eid] = row
        self._write(keep)
        return removed

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
