"""JSON Commit Node store — content-addressed by commit hash (AD-7)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mycelium.adapters.git.history import CommitRecord


class JsonCommitStore:
    """Per-workspace commit node persistence."""

    def __init__(self, workspace_dir: Path) -> None:
        self._dir = workspace_dir
        self._path = workspace_dir / "commits.json"
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

    def upsert_commits(self, commits: list[CommitRecord]) -> int:
        """Upsert commits by hash; return total stored count."""
        data = self._read()
        for c in commits:
            data[c.hash] = {
                "id": f"commit:{c.hash}",
                "kind": "Commit",
                "hash": c.hash,
                "author": c.author,
                "timestamp": c.timestamp,
                "message": c.message,
                "changed_paths": list(c.changed_paths),
            }
        self._write(data)
        return len(data)

    def list_commits(self, *, limit: int = 50) -> list[dict[str, Any]]:
        rows = list(self._read().values())
        rows.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
        return rows[: max(0, limit)]

    def count(self) -> int:
        return len(self._read())
