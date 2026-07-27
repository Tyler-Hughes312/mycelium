"""Context receipt — compact attestation for grounded agent turns."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from mycelium.adapters.http.app import create_app
from mycelium.core.domain.context_receipt import (
    format_receipt_line,
    format_verify,
    mint_receipt,
)
from mycelium.bridges.mcp.formatters import format_packet

from test_scaffold import (
    _commit_file,
    _init_git_repo,
    _wait_index,
    ensure_test_layout,
)


def test_mint_receipt_has_no_snippets() -> None:
    receipt = mint_receipt(
        tool="search",
        workspace_id="w1",
        head="abc123",
        results=[
            {
                "id": "sym:1",
                "path": "app.py",
                "kind": "Function",
                "title": "greet",
                "snippet": "SECRET BODY " * 50,
            }
        ],
        query="greet",
        served_tokens=40,
    )
    blob = str(receipt)
    assert "SECRET BODY" not in blob
    assert receipt["id"].startswith("rcp_")
    assert receipt["item_count"] == 1
    line = format_receipt_line(receipt)
    assert line.startswith("receipt=rcp_")
    assert "SECRET" not in line
    assert len(line) < 200


def test_format_packet_appends_one_receipt_line() -> None:
    text = format_packet(
        "Search: x",
        {
            "count": 1,
            "mode": "hybrid_rag",
            "results": [
                {
                    "kind": "Function",
                    "title": "greet",
                    "path": "app.py",
                    "snippet": "def greet(): return 1",
                    "id": "s1",
                }
            ],
            "receipt": {
                "id": "rcp_deadbeefcafe",
                "head": "abc",
                "item_count": 1,
                "served_tokens": 12,
            },
        },
    )
    assert text.count("receipt=") == 1
    assert "rcp_deadbeefcafe" in text


def test_verify_is_tiny() -> None:
    text = format_verify(
        {
            "id": "rcp_x",
            "tool": "search",
            "workspace_id": "w",
            "head": "aaa",
            "item_count": 1,
            "served_tokens": 10,
            "items": [
                {
                    "id": "1",
                    "path": "a.py",
                    "kind": "File",
                    "title": "a",
                }
            ],
        },
        current_head="bbb",
    )
    assert "status=stale" in text
    assert "No bodies" in text
    assert len(text) < 800


def test_http_search_receipt_and_grounded_summary(tmp_path: Path) -> None:
    cfg = ensure_test_layout(tmp_path / "home")
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    _commit_file(repo, "app.py", "def greet():\n    return 1\n", "add")

    with TestClient(create_app(cfg)) as client:
        ws = client.post("/workspaces", json={"path": str(repo)}).json()["workspace"]
        client.post(f"/workspaces/{ws['id']}/index")
        assert _wait_index(client, ws["id"])["status"] == "complete"

        result = client.post(
            "/query",
            json={"query": "greet", "workspace_id": ws["id"], "limit": 5},
        ).json()
        receipt = result.get("receipt") or {}
        assert receipt.get("id", "").startswith("rcp_")
        assert "items" not in receipt  # public slice is compact
        assert receipt.get("item_count", 0) >= 0

        full = client.get(f"/context/receipts/{receipt['id']}").json()["receipt"]
        assert full["id"] == receipt["id"]
        assert "items" in full
        for item in full["items"]:
            assert "snippet" not in item

        summary = client.get("/impact/summary", params={"range": "all"}).json()[
            "summary"
        ]
        assert summary["grounded_events"] >= 1
        assert summary["grounded_pct"] > 0
