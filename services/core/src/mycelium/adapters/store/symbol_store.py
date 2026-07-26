"""JSON File + Symbol Node store (AD-7 stable IDs)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mycelium.adapters.parse.symbols import SymbolRecord


class JsonSymbolStore:
    def __init__(self, workspace_dir: Path) -> None:
        self._dir = workspace_dir
        self._files_path = workspace_dir / "files.json"
        self._symbols_path = workspace_dir / "symbols.json"
        self._dir.mkdir(parents=True, exist_ok=True)
        if not self._files_path.exists():
            self._write(self._files_path, {})
        if not self._symbols_path.exists():
            self._write(self._symbols_path, {})

    def _read(self, path: Path) -> dict[str, dict[str, Any]]:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}

    def _write(self, path: Path, data: dict[str, dict[str, Any]]) -> None:
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def replace_snapshot(
        self,
        *,
        files: list[dict[str, Any]],
        symbols: list[SymbolRecord],
    ) -> tuple[int, int]:
        """Replace file/symbol maps for a full index pass (upsert by stable id)."""
        file_map = {f["id"]: f for f in files}
        symbol_map = {
            s.node_id: {
                "id": s.node_id,
                "kind": "Symbol",
                "path": s.path,
                "name": s.name,
                "symbol_kind": s.kind,
                "language": s.language,
                "start_line": s.start_line,
                "end_line": s.end_line,
            }
            for s in symbols
        }
        self._write(self._files_path, file_map)
        self._write(self._symbols_path, symbol_map)
        return len(file_map), len(symbol_map)

    def upsert_file_symbols(
        self,
        *,
        file_node: dict[str, Any] | None,
        path: str,
        symbols: list[SymbolRecord],
        deleted: bool = False,
    ) -> tuple[int, int]:
        """
        Incremental update for one path (AD-7): replace symbols for `path` only.
        Returns (file_count, symbol_count) after write.
        """
        files = self._read(self._files_path)
        symbols_map = self._read(self._symbols_path)
        file_id = f"file:{path}"

        # Drop prior symbols for this path so renames/deletes don't orphan nodes.
        symbols_map = {
            sid: row
            for sid, row in symbols_map.items()
            if row.get("path") != path
        }

        if deleted:
            files.pop(file_id, None)
        else:
            if file_node is None:
                raise ValueError("file_node required unless deleted")
            files[file_id] = file_node
            for s in symbols:
                symbols_map[s.node_id] = {
                    "id": s.node_id,
                    "kind": "Symbol",
                    "path": s.path,
                    "name": s.name,
                    "symbol_kind": s.kind,
                    "language": s.language,
                    "start_line": s.start_line,
                    "end_line": s.end_line,
                }

        self._write(self._files_path, files)
        self._write(self._symbols_path, symbols_map)
        return len(files), len(symbols_map)

    def list_symbols(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return self.list_all()[: max(0, limit)]

    def list_all(self) -> list[dict[str, Any]]:
        rows = list(self._read(self._symbols_path).values())
        rows.sort(key=lambda r: (r.get("path", ""), r.get("start_line", 0), r.get("name", "")))
        return rows

    def list_files(self, *, limit: int = 100) -> list[dict[str, Any]]:
        rows = list(self._read(self._files_path).values())
        rows.sort(key=lambda r: r.get("path", ""))
        return rows[: max(0, limit)]

    def symbol_count(self) -> int:
        return len(self._read(self._symbols_path))

    def file_count(self) -> int:
        return len(self._read(self._files_path))
