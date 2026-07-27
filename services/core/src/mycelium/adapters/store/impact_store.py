"""Local impact event log under ~/.mycelium/data (counts only)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

from mycelium.adapters.store.json_io import atomic_write_json, read_json_object

RangeName = Literal["today", "week", "all"]

_SOURCE_PRIORITY = {"inferred": 3, "default": 2, "unknown": 1}


def _dominant_model_source(counts: dict[str, int]) -> str:
    if not counts:
        return "unknown"
    max_count = max(counts.values())
    candidates = [source for source, count in counts.items() if count == max_count]
    return max(candidates, key=lambda source: _SOURCE_PRIORITY.get(source, 0))


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
        usd_saved_total = 0.0
        grounded = ungrounded = 0
        by_tool: dict[str, dict[str, Any]] = {}
        by_model: dict[str, dict[str, Any]] = {}
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
            if ev.get("grounded") or ev.get("receipt_id"):
                grounded += 1
            else:
                ungrounded += 1
            ev_served = int(ev.get("served_tokens") or 0)
            ev_baseline = int(ev.get("baseline_tokens") or 0)
            ev_saved = int(ev.get("tokens_saved") or 0)
            ev_usd = float(ev.get("usd_saved") or 0)
            served += ev_served
            baseline += ev_baseline
            saved += ev_saved
            usd_saved_total += ev_usd

            tool = str(ev.get("tool") or "")
            tool_row = by_tool.setdefault(
                tool,
                {"tool": tool, "event_count": 0, "tokens_saved": 0, "usd_saved": 0.0},
            )
            tool_row["event_count"] += 1
            tool_row["tokens_saved"] += ev_saved
            tool_row["usd_saved"] += ev_usd

            model_id = str(ev.get("model_id") or "")
            model_row = by_model.setdefault(
                model_id,
                {
                    "model_id": model_id,
                    "event_count": 0,
                    "tokens_saved": 0,
                    "usd_saved": 0.0,
                    "_source_counts": {},
                },
            )
            model_row["event_count"] += 1
            model_row["tokens_saved"] += ev_saved
            model_row["usd_saved"] += ev_usd
            source = str(ev.get("model_source") or "unknown")
            source_counts = model_row["_source_counts"]
            source_counts[source] = int(source_counts.get(source, 0)) + 1

        pct = round((saved / baseline) * 100, 1) if baseline > 0 else 0.0
        grounded_pct = round((grounded / count) * 100, 1) if count > 0 else 0.0
        by_tool_list = sorted(
            by_tool.values(), key=lambda row: row["tokens_saved"], reverse=True
        )
        by_model_list: list[dict[str, Any]] = []
        for row in by_model.values():
            source_counts = row.pop("_source_counts")
            by_model_list.append(
                {
                    "model_id": row["model_id"],
                    "model_source_dominant": _dominant_model_source(source_counts),
                    "event_count": row["event_count"],
                    "tokens_saved": row["tokens_saved"],
                    "usd_saved": row["usd_saved"],
                }
            )
        by_model_list.sort(key=lambda row: row["tokens_saved"], reverse=True)
        return {
            "range": range_name,
            "event_count": count,
            "served_tokens": served,
            "baseline_tokens": baseline,
            "tokens_saved": saved,
            "savings_pct": pct,
            "usd_saved": usd_saved_total,
            "grounded_events": grounded,
            "ungrounded_events": ungrounded,
            "grounded_pct": grounded_pct,
            "by_tool": by_tool_list,
            "by_model": by_model_list,
        }
