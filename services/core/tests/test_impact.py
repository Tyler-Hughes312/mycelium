from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from mycelium.adapters.store.impact_store import ImpactStore
from mycelium.core.domain.impact_service import (
    compute_tokens_saved,
    estimate_pack_impact,
    estimate_query_impact,
)


def test_tokens_saved_clamps_at_zero() -> None:
    assert compute_tokens_saved(served=100, baseline=40) == 0
    assert compute_tokens_saved(served=40, baseline=100) == 60


def test_pack_baseline_uses_max_tokens() -> None:
    served, baseline, saved = estimate_pack_impact(tokens_est=200, max_tokens=2000)
    assert served == 200
    assert baseline == 2000
    assert saved == 1800


def test_query_impact_without_paths_uses_4x_served() -> None:
    served, baseline, saved = estimate_query_impact(
        snippets=["abcd" * 25],  # 100 chars -> 25 tokens
        path_texts={},
    )
    assert served == 25
    assert baseline == 100
    assert saved == 75


def test_store_summary_ranges_and_clear(tmp_path: Path) -> None:
    store = ImpactStore(tmp_path / "impact_events.json")
    now = datetime.now(timezone.utc)
    store.append(
        {
            "ts": now.isoformat(),
            "tool": "search",
            "workspace_id": "ws1",
            "served_tokens": 10,
            "baseline_tokens": 100,
            "tokens_saved": 90,
        }
    )
    old = (now - timedelta(days=10)).isoformat()
    store.append(
        {
            "ts": old,
            "tool": "focus",
            "workspace_id": "ws1",
            "served_tokens": 5,
            "baseline_tokens": 50,
            "tokens_saved": 45,
        }
    )
    today = store.summary("today")
    assert today["event_count"] == 1
    assert today["tokens_saved"] == 90
    week = store.summary("week")
    assert week["event_count"] == 1
    all_ = store.summary("all")
    assert all_["event_count"] == 2
    assert all_["tokens_saved"] == 135
    store.clear()
    assert store.summary("all")["event_count"] == 0


def test_impact_http_records_and_respects_disable(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    from mycelium.adapters.http.app import create_app
    from mycelium.core.config import ensure_local_layout

    home = tmp_path / "home"
    cfg = ensure_local_layout(home)
    text = cfg.paths.config_file.read_text(encoding="utf-8")
    text = text.replace(
        'model = "sentence-transformers/all-MiniLM-L6-v2"',
        'model = "mycelium-hashing-v1"',
    )
    if 'model = "mycelium-hashing-v1"' not in text:
        text = text.rstrip() + '\n\n[embedding]\nmodel = "mycelium-hashing-v1"\n'
    cfg.paths.config_file.write_text(text, encoding="utf-8")
    cfg = ensure_local_layout(home)

    app = create_app(cfg)
    with TestClient(app) as client:
        pack = client.post("/vault/pack", json={"max_tokens": 500}).json()
        assert "pack" in pack
        summary = client.get("/impact/summary", params={"range": "all"}).json()[
            "summary"
        ]
        assert summary["event_count"] >= 1

        client.patch("/settings", json={"impact_tracking_enabled": False})
        before = client.get("/impact/summary", params={"range": "all"}).json()[
            "summary"
        ]["event_count"]
        client.post("/vault/pack", json={"max_tokens": 500})
        after = client.get("/impact/summary", params={"range": "all"}).json()[
            "summary"
        ]["event_count"]
        assert after == before

        client.delete("/impact/events")
        cleared = client.get("/impact/summary", params={"range": "all"}).json()[
            "summary"
        ]
        assert cleared["event_count"] == 0


def test_store_summary_includes_usd_and_breakdowns(tmp_path: Path) -> None:
    store = ImpactStore(tmp_path / "impact_events.json")
    now = datetime.now(timezone.utc).isoformat()
    store.append(
        {
            "ts": now,
            "tool": "search",
            "workspace_id": "ws1",
            "served_tokens": 10,
            "baseline_tokens": 110,
            "tokens_saved": 100,
            "model_id": "claude-sonnet-4",
            "model_source": "default",
            "usd_per_1m_input": 3.0,
            "usd_saved": 0.0003,
        }
    )
    store.append(
        {
            "ts": now,
            "tool": "focus",
            "workspace_id": "ws1",
            "served_tokens": 5,
            "baseline_tokens": 55,
            "tokens_saved": 50,
            "model_id": "claude-sonnet-4",
            "model_source": "default",
            "usd_per_1m_input": 3.0,
            "usd_saved": 0.00015,
        }
    )
    summary = store.summary("all")
    assert abs(summary["usd_saved"] - 0.00045) < 1e-9
    tools = {row["tool"]: row for row in summary["by_tool"]}
    assert tools["search"]["tokens_saved"] == 100
    assert tools["focus"]["event_count"] == 1
    models = {row["model_id"]: row for row in summary["by_model"]}
    assert models["claude-sonnet-4"]["tokens_saved"] == 150


def test_impact_pricing_endpoint_and_default_model_on_pack(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    from mycelium.adapters.http.app import create_app
    from mycelium.core.config import ensure_local_layout

    home = tmp_path / "home"
    cfg = ensure_local_layout(home)
    text = cfg.paths.config_file.read_text(encoding="utf-8")
    if "mycelium-hashing-v1" not in text:
        text = text.rstrip() + '\n\n[embedding]\nmodel = "mycelium-hashing-v1"\n'
        cfg.paths.config_file.write_text(text, encoding="utf-8")
        cfg = ensure_local_layout(home)

    app = create_app(cfg)
    with TestClient(app) as client:
        pricing = client.get("/impact/pricing").json()
        assert pricing["default_model"] == "claude-sonnet-4"
        assert any(r["id"] == "gpt-4o" for r in pricing["rates"])

        client.patch(
            "/settings",
            json={
                "impact_default_model": "gpt-4o",
                "impact_pricing_overrides": {"gpt-4o": 1.0},
            },
        )
        client.delete("/impact/events")
        client.post("/vault/pack", json={"max_tokens": 500})
        events = client.get("/impact/events").json()["events"]
        assert events
        assert events[0]["model_id"] == "gpt-4o"
        assert events[0]["model_source"] == "default"
        assert events[0]["usd_per_1m_input"] == 1.0

        client.delete("/impact/events")
        client.post(
            "/vault/pack",
            json={"max_tokens": 500},
            headers={"X-Mycelium-Model-Id": "claude-opus-4"},
        )
        ev = client.get("/impact/events").json()["events"][0]
        assert ev["model_id"] == "claude-opus-4"
        assert ev["model_source"] == "inferred"


def test_legacy_events_usd_defaults_zero(tmp_path: Path) -> None:
    store = ImpactStore(tmp_path / "impact_events.json")
    store.append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tool": "search",
            "workspace_id": "",
            "served_tokens": 1,
            "baseline_tokens": 10,
            "tokens_saved": 9,
        }
    )
    summary = store.summary("all")
    assert summary["usd_saved"] == 0.0
    assert summary["by_model"][0]["model_id"] == ""


def test_backfill_pricing_fills_legacy_events(tmp_path: Path) -> None:
    store = ImpactStore(tmp_path / "impact_events.json")
    store.append(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tool": "search",
            "workspace_id": "",
            "served_tokens": 1,
            "baseline_tokens": 1_000_001,
            "tokens_saved": 1_000_000,
        }
    )
    changed = store.backfill_pricing(
        default_model="claude-sonnet-4",
        usd_per_1m_input=3.0,
    )
    assert changed == 1
    summary = store.summary("all")
    assert abs(summary["usd_saved"] - 3.0) < 1e-9
    assert summary["by_model"][0]["model_id"] == "claude-sonnet-4"
    # Idempotent
    assert store.backfill_pricing(
        default_model="claude-sonnet-4", usd_per_1m_input=3.0
    ) == 0
