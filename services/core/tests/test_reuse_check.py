"""Tests for mycelium_reuse_check packet formatting."""

from __future__ import annotations

from mycelium.bridges.mcp.formatters import (
    classify_reuse_hits,
    format_reuse_packet,
    is_code_like_hit,
    is_junk_path,
)


def test_junk_path_filters_build_artifacts() -> None:
    assert is_junk_path("apps/desktop/src-tauri/target/release/foo.py") is True
    assert is_junk_path("node_modules/pkg/index.js") is True
    assert is_junk_path("services/core/src/mycelium/bridges/mcp/server.py") is False


def test_code_like_hit() -> None:
    assert is_code_like_hit({"kind": "Symbol", "path": "src/a.py"}) is True
    assert is_code_like_hit({"kind": "Note", "path": "brain/Patterns.md"}) is False
    assert is_code_like_hit({"kind": "File", "path": "target/debug/x.py"}) is False


def test_classify_strong_other_repo() -> None:
    results = [
        {
            "kind": "Symbol",
            "title": "auth",
            "path": "src/auth.py",
            "workspace_id": "other",
            "workspace_name": "old-app",
            "snippet": "def login():",
        }
    ]
    out = classify_reuse_hits(results, current_workspace_id="current")
    assert out["strong"] is True
    assert len(out["other"]) == 1
    assert out["local"] == []


def test_classify_strong_two_local() -> None:
    results = [
        {
            "kind": "File",
            "title": "a",
            "path": "a.py",
            "workspace_id": "ws1",
        },
        {
            "kind": "Function",
            "title": "b",
            "path": "b.py",
            "workspace_id": "ws1",
        },
    ]
    out = classify_reuse_hits(results, current_workspace_id="ws1")
    assert out["strong"] is True
    assert len(out["local"]) == 2


def test_classify_weak_single_local() -> None:
    results = [
        {
            "kind": "Symbol",
            "title": "only",
            "path": "only.py",
            "workspace_id": "ws1",
        }
    ]
    out = classify_reuse_hits(results, current_workspace_id="ws1")
    assert out["strong"] is False


def test_format_reuse_packet_asks_on_strong() -> None:
    packet = {
        "results": [
            {
                "kind": "Symbol",
                "title": "RateLimiter",
                "path": "limiter.py",
                "workspace_id": "other",
                "workspace_name": "dogfood",
                "snippet": "class RateLimiter",
            }
        ],
        "receipt": {"id": "rcp_test", "head": "abc", "item_count": 1, "served_tokens": 10},
    }
    text = format_reuse_packet(
        "add rate limiting",
        query_packet=packet,
        current_workspace_id="here",
    )
    assert "Reuse check: add rate limiting" in text
    assert "ASK USER" in text
    assert "@dogfood" in text
    assert "receipt=" in text


def test_format_reuse_packet_greenfield_when_empty() -> None:
    text = format_reuse_packet(
        "brand new widget",
        query_packet={"results": [], "receipt": None},
        current_workspace_id="here",
    )
    assert "No strong prior art" in text
    assert "ASK USER" not in text
