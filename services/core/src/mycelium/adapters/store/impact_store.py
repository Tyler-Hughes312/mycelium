"""Local impact event log under ~/.mycelium/data (counts only)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

from mycelium.adapters.store.json_io import atomic_write_json, read_json_object

RangeName = Literal["today", "week", "all"]


class ImpactStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _load(self) -> list[dict[str, Any]]:
        data = read_json_object(self.path, default={"events": []})
        events = data.get("events") if isinstance(data, dict) else []
        return list(events) if isinstance(events, list) else []

    def _save(self, events: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(self.path, {"events": events})

    def append(self, event: dict[str, Any]) -> None:
        events = self._load()
        events.append(event)
        if len(events) > 5000:
            events = events[-5000:]
        self._save(events)

    def list_events(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 500))
        events = self._load()
        return list(reversed(events[-limit:]))

    def clear(self) -> None:
        self._save([])

    def summary(self, range_name: RangeName = "all") -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        if range_name == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif range_name == "week":
            start = now - timedelta(days=7)
        else:
            start = None

        served = baseline = saved = count = 0
        for ev in self._load():
            ts_raw = str(ev.get("ts") or "")
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            if start is not None and ts < start:
                continue
            count += 1
            served += int(ev.get("served_tokens") or 0)
            baseline += int(ev.get("baseline_tokens") or 0)
            saved += int(ev.get("tokens_saved") or 0)

        pct = round((saved / baseline) * 100, 1) if baseline > 0 else 0.0
        return {
            "range": range_name,
            "event_count": count,
            "served_tokens": served,
            "baseline_tokens": baseline,
            "tokens_saved": saved,
            "savings_pct": pct,
        }
