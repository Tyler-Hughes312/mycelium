from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


@dataclass
class LedgerEntry:
    wave_id: str
    channel: str
    target: str
    status: str
    url: str = ""
    detail: str = ""
    ts: str = ""

    def key(self) -> str:
        return f"{self.wave_id}|{self.channel}|{self.target}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_ledger(path: Path, entry: LedgerEntry) -> None:
    if not entry.ts:
        entry.ts = _now()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(entry)) + "\n")


def read_ledger(path: Path) -> list[LedgerEntry]:
    if not path.exists():
        return []
    out: list[LedgerEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        out.append(LedgerEntry(**data))
    return out


def already_posted(path: Path, wave_id: str, channel: str, target: str) -> bool:
    key = f"{wave_id}|{channel}|{target}"
    return any(e.key() == key and e.status == "posted" for e in read_ledger(path))


def reddit_posts_last_24h(path: Path, now: datetime | None = None) -> list[LedgerEntry]:
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    out: list[LedgerEntry] = []
    for e in read_ledger(path):
        if e.channel != "reddit" or e.status != "posted":
            continue
        try:
            ts = datetime.fromisoformat(e.ts)
        except ValueError:
            continue
        if ts >= cutoff:
            out.append(e)
    return out


def minutes_since_last_reddit(path: Path, now: datetime | None = None) -> float | None:
    now = now or datetime.now(timezone.utc)
    latest: datetime | None = None
    for e in reddit_posts_last_24h(path, now=now):
        ts = datetime.fromisoformat(e.ts)
        if latest is None or ts > latest:
            latest = ts
    if latest is None:
        return None
    return (now - latest).total_seconds() / 60.0


@dataclass
class QueueItem:
    id: str
    kind: str
    payload: dict[str, Any]
    status: str = "pending"
    ts: str = ""


def enqueue(path: Path, item: QueueItem) -> None:
    if not item.ts:
        item.ts = _now()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(item)) + "\n")


def read_queue(path: Path) -> list[QueueItem]:
    if not path.exists():
        return []
    items: list[QueueItem] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        data = json.loads(line)
        items.append(QueueItem(**data))
    return items


def set_queue_status(path: Path, item_id: str, status: str) -> bool:
    items = read_queue(path)
    found = False
    for it in items:
        if it.id == item_id and it.status == "pending":
            it.status = status
            found = True
    if found:
        with path.open("w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(asdict(it)) + "\n")
    return found
