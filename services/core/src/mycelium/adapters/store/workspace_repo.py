"""Filesystem-backed WorkspaceRepo (FR-2)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class WorkspaceError(Exception):
    """Structured registration/list failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _is_git_repo(path: Path) -> bool:
    git = path / ".git"
    return git.is_dir() or git.is_file()


def _display_name(path: Path) -> str:
    parts = path.parts
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return path.name


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class JsonFileWorkspaceRepo:
    """Persist workspaces as JSON under the Core data directory."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._path = data_dir / "workspaces.json"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write([])

    def _read(self) -> list[dict[str, Any]]:
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return []
        return raw

    def _write(self, rows: list[dict[str, Any]]) -> None:
        self._path.write_text(
            json.dumps(rows, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def list_workspaces(self) -> list[dict[str, Any]]:
        return self._read()

    def get(self, workspace_id: str) -> dict[str, Any] | None:
        for row in self._read():
            if row.get("id") == workspace_id:
                return row
        return None

    def update(self, workspace_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        rows = self._read()
        for i, row in enumerate(rows):
            if row.get("id") == workspace_id:
                updated = {**row, **patch}
                rows[i] = updated
                self._write(rows)
                return updated
        raise WorkspaceError("not_found", f"Unknown workspace id: {workspace_id}")

    def register(self, path: str) -> dict[str, Any]:
        if not path or not path.strip():
            raise WorkspaceError("empty_path", "Workspace path is required")

        expanded = Path(path).expanduser()
        try:
            resolved = expanded.resolve(strict=False)
        except OSError as exc:
            raise WorkspaceError("invalid_path", f"Cannot resolve path: {exc}") from exc

        if not resolved.exists():
            raise WorkspaceError("not_found", f"Path does not exist: {resolved}")
        if not resolved.is_dir():
            raise WorkspaceError("not_directory", f"Path is not a directory: {resolved}")
        if not _is_git_repo(resolved):
            raise WorkspaceError(
                "not_git_repo",
                f"Path is not a git repository (missing .git): {resolved}",
            )

        path_str = str(resolved)
        existing = self._read()
        for row in existing:
            if row.get("path") == path_str:
                return row

        row: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "name": _display_name(resolved),
            "path": path_str,
            "status": "idle",
            "symbols": 0,
            "commits": 0,
            "notes": 0,
            "indexed_ago": "never",
            "registered_at": _now_iso(),
        }
        existing.append(row)
        self._write(existing)
        return row
