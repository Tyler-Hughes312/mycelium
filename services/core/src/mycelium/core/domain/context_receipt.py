"""Compact context receipts — attestation only, never a second packet dump."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from mycelium.adapters.store.json_io import atomic_write_json, read_json_object


def _short_hash(payload: str, *, n: int = 12) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:n]


def mint_receipt(
    *,
    tool: str,
    workspace_id: str,
    head: str,
    results: list[dict[str, Any]],
    query: str = "",
    served_tokens: int = 0,
) -> dict[str, Any]:
    """Build a small receipt. Stores ids/paths only — no snippets or bodies."""
    items: list[dict[str, str]] = []
    for row in results[:12]:
        if not isinstance(row, dict):
            continue
        rid = str(row.get("id") or "")
        path = str(row.get("path") or "")
        kind = str(row.get("kind") or "")
        title = str(row.get("title") or "")[:80]
        if not rid and not path:
            continue
        items.append({"id": rid, "path": path, "kind": kind, "title": title})

    query_fp = _short_hash(query.strip().lower()) if query.strip() else ""
    material = json.dumps(
        {
            "tool": tool,
            "workspace_id": workspace_id,
            "head": head,
            "ids": [i["id"] for i in items],
            "query_fp": query_fp,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    receipt_id = "rcp_" + _short_hash(material)
    return {
        "id": receipt_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "workspace_id": workspace_id or "",
        "head": (head or "")[:40],
        "query_fp": query_fp,
        "served_tokens": max(0, int(served_tokens)),
        "item_count": len(items),
        "items": items,
    }


def format_receipt_line(receipt: dict[str, Any] | None) -> str:
    """One-line footer for agent windows — cite this; do not re-dump context."""
    if not receipt:
        return ""
    return (
        f"receipt={receipt.get('id')} head={receipt.get('head') or '-'} "
        f"items={receipt.get('item_count', 0)} served~{receipt.get('served_tokens', 0)} "
        f"(cite receipt; do not re-fetch full vault/code)"
    )


def format_verify(receipt: dict[str, Any], *, current_head: str) -> str:
    """Tiny verification payload — paths/titles only, no snippets."""
    stored = str(receipt.get("head") or "")
    cur = (current_head or "")[:40]
    status = "valid" if stored and stored == cur else ("stale" if stored else "unknown")
    lines = [
        f"# Receipt {receipt.get('id')}",
        f"status={status} tool={receipt.get('tool')} workspace={receipt.get('workspace_id')}",
        f"head_receipt={stored or '-'} head_now={cur or '-'}",
        f"items={receipt.get('item_count', 0)} served~{receipt.get('served_tokens', 0)}",
    ]
    for i, item in enumerate(list(receipt.get("items") or [])[:8], start=1):
        lines.append(
            f"{i}. [{item.get('kind')}] {item.get('title')} — {item.get('path')}"
        )
    lines.append("No bodies/snippets — use mycelium_focus on a path only if needed.")
    return "\n".join(lines)


class ReceiptStore:
    def __init__(self, path) -> None:
        self.path = path

    def _load(self) -> dict[str, Any]:
        data = read_json_object(self.path, default={"receipts": {}})
        receipts = data.get("receipts") if isinstance(data, dict) else {}
        return dict(receipts) if isinstance(receipts, dict) else {}

    def _save(self, receipts: dict[str, Any]) -> None:
        # Cap by insertion order of keys (dict preserves order in 3.7+)
        if len(receipts) > 500:
            keys = list(receipts.keys())
            for k in keys[: len(keys) - 500]:
                receipts.pop(k, None)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(self.path, {"receipts": receipts})

    def put(self, receipt: dict[str, Any]) -> dict[str, Any]:
        receipts = self._load()
        rid = str(receipt.get("id") or "")
        if not rid:
            raise ValueError("receipt missing id")
        receipts[rid] = receipt
        self._save(receipts)
        return {
            "id": rid,
            "head": receipt.get("head"),
            "item_count": receipt.get("item_count"),
            "served_tokens": receipt.get("served_tokens"),
            "tool": receipt.get("tool"),
            "workspace_id": receipt.get("workspace_id"),
        }

    def get(self, receipt_id: str) -> dict[str, Any] | None:
        return self._load().get(receipt_id)
