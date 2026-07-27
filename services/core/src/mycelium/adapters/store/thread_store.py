"""JSON-backed thread + turn persistence for Mycelium Chat."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mycelium.adapters.store.json_io import atomic_write_json, read_json_object
from mycelium.core.domain.vault_service import estimate_tokens


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _id_slug(thread_id: str) -> str:
    return thread_id.replace(":", "_")


class ThreadStore:
    """Persist threads as JSON under data/threads/{id_slug}.json + index.json."""

    def __init__(self, path: Path) -> None:
        self._dir = path
        self._index_path = path / "index.json"
        self._dir.mkdir(parents=True, exist_ok=True)
        if not self._index_path.exists():
            atomic_write_json(self._index_path, {"threads": []})

    def _thread_path(self, thread_id: str) -> Path:
        return self._dir / f"{_id_slug(thread_id)}.json"

    def _load_index(self) -> list[dict[str, Any]]:
        data = read_json_object(self._index_path, default={"threads": []})
        threads = data.get("threads") if isinstance(data, dict) else []
        return list(threads) if isinstance(threads, list) else []

    def _save_index(self, threads: list[dict[str, Any]]) -> None:
        atomic_write_json(self._index_path, {"threads": threads})

    def _load_thread(self, thread_id: str) -> dict[str, Any] | None:
        path = self._thread_path(thread_id)
        if not path.exists():
            return None
        doc = read_json_object(path, default={})
        return doc if isinstance(doc, dict) else None

    def _save_thread(self, doc: dict[str, Any]) -> None:
        atomic_write_json(self._thread_path(str(doc["id"])), doc)

    def _with_turn_count(self, doc: dict[str, Any]) -> dict[str, Any]:
        turns = doc.get("turns")
        count = len(turns) if isinstance(turns, list) else 0
        return {**doc, "turn_count": count}

    def create(self, *, workspace_id: str, title: str) -> dict[str, Any]:
        thread_id = f"thread:{uuid.uuid4()}"
        now = _now_iso()
        doc: dict[str, Any] = {
            "id": thread_id,
            "workspace_id": workspace_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "turns": [],
        }
        self._save_thread(doc)
        index = self._load_index()
        index.append(
            {
                "id": thread_id,
                "workspace_id": workspace_id,
                "title": title,
                "created_at": now,
                "updated_at": now,
                "turn_count": 0,
            }
        )
        self._save_index(index)
        return self._with_turn_count(doc)

    def get(self, thread_id: str) -> dict[str, Any] | None:
        doc = self._load_thread(thread_id)
        if doc is None:
            return None
        return self._with_turn_count(doc)

    def list(self) -> list[dict[str, Any]]:
        return self._load_index()

    def list_turns(self, thread_id: str) -> list[dict[str, Any]]:
        doc = self._load_thread(thread_id)
        if doc is None:
            return []
        turns = doc.get("turns")
        return list(turns) if isinstance(turns, list) else []

    def append_turn(self, thread_id: str, *, role: str, text: str) -> dict[str, Any]:
        doc = self._load_thread(thread_id)
        if doc is None:
            raise ValueError(f"Unknown thread: {thread_id}")

        turns = doc.get("turns")
        if not isinstance(turns, list):
            turns = []
            doc["turns"] = turns

        seq = len(turns) + 1
        turn: dict[str, Any] = {
            "id": f"turn:{thread_id}:{seq}",
            "seq": seq,
            "role": role,
            "text": text,
            "token_est": estimate_tokens(text),
        }
        turns.append(turn)

        now = _now_iso()
        doc["updated_at"] = now
        self._save_thread(doc)

        index = self._load_index()
        for row in index:
            if row.get("id") == thread_id:
                row["updated_at"] = now
                row["turn_count"] = len(turns)
                break
        self._save_index(index)

        return turn
