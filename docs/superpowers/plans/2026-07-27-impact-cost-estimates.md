# Impact Cost Estimates ($ + Model Attribution) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend local Impact telemetry so Desktop shows tokens saved, which LLM those avoided tokens would have billed against (inferred or assumed), and estimated dollars saved using editable API list prices.

**Architecture:** Snapshot `model_id`, `model_source`, `usd_per_1m_input`, and `usd_saved` onto each Impact event at record time. A small pricing module ships curated `$ / 1M input` rates with Settings overrides. MCP probes `_meta`/context for model hints (best-effort); otherwise Settings `impact_default_model`. Summary adds `usd_saved`, `by_tool`, and `by_model`. Desktop Impact + Settings UI surface the new fields with honest Assumed/Unknown labels.

**Tech Stack:** Python 3 / FastAPI Core, pytest (`services/core/tests`), React + TypeScript Desktop (`apps/desktop`), Vite.

**Spec:** `docs/superpowers/specs/2026-07-27-impact-cost-estimates-design.md`

## Global Constraints

- Local-only under `~/.mycelium` — no cloud export / analytics vendor
- Events: counts + metadata only (no prompt text, no file bodies in the store)
- Baseline unchanged: dump matched files / pack ceiling (existing `estimate_query_impact` / `estimate_pack_impact`)
- `$` formula: `usd_saved = tokens_saved / 1_000_000 * usd_per_1m_input` (input list price only)
- Model resolution: MCP probe → Settings default → unknown
- UI always labels estimates; never claim Cursor subscription billing accuracy
- Skip git commits unless the user asks
- Do not sync Desktop numbers to the marketing site

---

## File map

| File | Responsibility |
|------|----------------|
| `services/core/src/mycelium/core/domain/impact_pricing.py` | Shipped rate table, resolve rate, compute `usd_saved`, probe model hints |
| `services/core/src/mycelium/core/domain/impact_service.py` | Attach model + $ snapshot in `_record` |
| `services/core/src/mycelium/adapters/store/impact_store.py` | Aggregate `usd_saved`, `by_tool`, `by_model` in `summary` |
| `services/core/src/mycelium/core/config.py` | `ImpactSettings.default_model` + `pricing_overrides`; settings PATCH |
| `services/core/src/mycelium/adapters/http/app.py` | `/impact/pricing`; pass model probe into ImpactService; settings fields |
| `services/core/src/mycelium/bridges/mcp/client.py` | Forward optional model headers to Core |
| `services/core/src/mycelium/bridges/mcp/server.py` | Best-effort FastMCP `_meta` → `X-Mycelium-Model-Id` |
| `services/core/tests/test_impact_pricing.py` | Pricing + resolution unit tests |
| `services/core/tests/test_impact.py` | Extend store summary + HTTP $ fields |
| `apps/desktop/src/api/client.ts` | Types + `getImpactPricing` + settings fields |
| `apps/desktop/src/pages/ImpactPage.tsx` | $ hero, by_tool, by_model, event $ / model badges |
| `apps/desktop/src/pages/SettingsPage.tsx` | Default model + rate editor |

**MCP probe note:** Mycelium MCP tools call Core over HTTP. v1 accepts header `X-Mycelium-Model-Id`. MCP bridge sets it when FastMCP exposes a recognizable model key in request `_meta`. If nothing found, Core uses Settings default. Do not invent model ids. Cursor usually does not send model today.

---

### Task 1: Pricing module (TDD)

**Files:**
- Create: `services/core/src/mycelium/core/domain/impact_pricing.py`
- Create: `services/core/tests/test_impact_pricing.py`

**Interfaces:**
- Consumes: none (pure helpers)
- Produces:
  - `DEFAULT_INPUT_RATES_USD_PER_1M: dict[str, float]`
  - `compute_usd_saved(*, tokens_saved: int, usd_per_1m_input: float) -> float`
  - `effective_rates(overrides: dict[str, float] | None) -> dict[str, float]`
  - `rate_for_model(model_id: str, overrides: dict[str, float] | None) -> float`
  - `resolve_model(*, probe: dict | None, default_model: str) -> tuple[str, str, str]` → `(model_id, model_source, model_probe)` with `model_source` in `inferred|default|unknown`

- [ ] **Step 1: Write failing tests** in `services/core/tests/test_impact_pricing.py`

```python
from __future__ import annotations

from mycelium.core.domain.impact_pricing import (
    DEFAULT_INPUT_RATES_USD_PER_1M,
    compute_usd_saved,
    effective_rates,
    rate_for_model,
    resolve_model,
)


def test_compute_usd_saved() -> None:
    assert abs(compute_usd_saved(tokens_saved=100_000, usd_per_1m_input=3.0) - 0.3) < 1e-9
    assert compute_usd_saved(tokens_saved=0, usd_per_1m_input=3.0) == 0.0
    assert compute_usd_saved(tokens_saved=1000, usd_per_1m_input=0.0) == 0.0


def test_overrides_beat_defaults() -> None:
    rates = effective_rates({"claude-sonnet-4": 9.99})
    assert rates["claude-sonnet-4"] == 9.99
    assert "gpt-4o" in rates
    assert rate_for_model("missing-model", None) == 0.0


def test_resolve_model_inferred_from_probe() -> None:
    mid, src, probe = resolve_model(
        probe={"model": "claude-sonnet-4"},
        default_model="gpt-4o",
    )
    assert mid == "claude-sonnet-4"
    assert src == "inferred"
    assert "model" in probe


def test_resolve_model_falls_back_to_default() -> None:
    mid, src, _ = resolve_model(probe=None, default_model="gpt-4o")
    assert mid == "gpt-4o"
    assert src == "default"


def test_resolve_model_unknown_when_empty() -> None:
    mid, src, _ = resolve_model(probe={}, default_model="")
    assert mid == ""
    assert src == "unknown"


def test_shipped_table_has_core_models() -> None:
    for key in ("claude-sonnet-4", "gpt-4o", "gemini-2.5-flash"):
        assert key in DEFAULT_INPUT_RATES_USD_PER_1M
        assert DEFAULT_INPUT_RATES_USD_PER_1M[key] > 0
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `cd services/core && ../../venv/bin/pytest tests/test_impact_pricing.py -v`  
Expected: FAIL (module not found)

- [ ] **Step 3: Implement `impact_pricing.py`**

```python
"""API list-price estimates for Impact $ savings (input tokens only)."""

from __future__ import annotations

from typing import Any

DEFAULT_INPUT_RATES_USD_PER_1M: dict[str, float] = {
    "claude-sonnet-4": 3.0,
    "claude-opus-4": 15.0,
    "claude-haiku-3.5": 0.8,
    "gpt-4o": 2.5,
    "gpt-4.1": 2.0,
    "gemini-2.5-flash": 0.15,
    "gemini-2.5-pro": 1.25,
}

_PROBE_KEYS = (
    "model",
    "model_id",
    "modelId",
    "llm",
    "cursor/model",
    "anthropic/model",
    "openai/model",
)


def compute_usd_saved(*, tokens_saved: int, usd_per_1m_input: float) -> float:
    if tokens_saved <= 0 or usd_per_1m_input <= 0:
        return 0.0
    return float(tokens_saved) / 1_000_000.0 * float(usd_per_1m_input)


def effective_rates(overrides: dict[str, float] | None) -> dict[str, float]:
    rates = dict(DEFAULT_INPUT_RATES_USD_PER_1M)
    if overrides:
        for k, v in overrides.items():
            key = str(k).strip()
            if not key:
                continue
            try:
                rates[key] = float(v)
            except (TypeError, ValueError):
                continue
    return rates


def rate_for_model(model_id: str, overrides: dict[str, float] | None) -> float:
    mid = (model_id or "").strip()
    if not mid:
        return 0.0
    return float(effective_rates(overrides).get(mid, 0.0))


def _extract_model_from_probe(probe: dict[str, Any] | None) -> tuple[str, str]:
    if not probe:
        return "", ""
    for key in _PROBE_KEYS:
        if key in probe and probe[key]:
            return str(probe[key]).strip(), key
    meta = probe.get("_meta") if isinstance(probe.get("_meta"), dict) else None
    if meta:
        for key in _PROBE_KEYS:
            if key in meta and meta[key]:
                return str(meta[key]).strip(), f"_meta.{key}"
    return "", ""


def resolve_model(
    *,
    probe: dict[str, Any] | None,
    default_model: str,
) -> tuple[str, str, str]:
    inferred, probe_key = _extract_model_from_probe(probe)
    if inferred:
        return inferred, "inferred", probe_key[:120]
    default = (default_model or "").strip()
    if default:
        return default, "default", ""
    return "", "unknown", ""
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `cd services/core && ../../venv/bin/pytest tests/test_impact_pricing.py -v`

- [ ] **Step 5: Commit only if user asked**

---

### Task 2: Config — default model + pricing overrides

**Files:**
- Modify: `services/core/src/mycelium/core/config.py`
- Modify: `services/core/src/mycelium/adapters/http/app.py` (SettingsPatch body)

**Interfaces:**
- Produces: `ImpactSettings(tracking_enabled=True, default_model="claude-sonnet-4", pricing_overrides={})`
- `settings_dict` keys `impact_default_model`, `impact_pricing_overrides`
- `update_config(..., impact_default_model=..., impact_pricing_overrides=...)`
- PATCH `/settings` accepts those fields

- [ ] **Step 1: Extend `ImpactSettings`**

```python
@dataclass(frozen=True)
class ImpactSettings:
    tracking_enabled: bool = True
    default_model: str = "claude-sonnet-4"
    pricing_overrides: dict[str, float] = field(default_factory=dict)
```

Import `field` from dataclasses if needed. Load/write `[impact]` + optional `[impact.pricing_overrides]` in TOML.

- [ ] **Step 2: Wire `update_config` + `settings_dict` + PATCH body**

When `impact_pricing_overrides` is provided (including `{}`), replace the whole overrides map.

- [ ] **Step 3: Regression**

Run: `cd services/core && ../../venv/bin/pytest tests/test_impact.py -v`  
Expected: PASS

- [ ] **Step 4: Commit only if user asked**

---

### Task 3: ImpactService + ImpactStore aggregates

**Files:**
- Modify: `services/core/src/mycelium/core/domain/impact_service.py`
- Modify: `services/core/src/mycelium/adapters/store/impact_store.py`
- Modify: `services/core/tests/test_impact.py`

**Interfaces:**
- `ImpactService(..., default_model: str, pricing_overrides: dict[str, float] | None)`
- `_record(..., probe: dict | None = None)` writes `model_id`, `model_source`, `model_probe`, `usd_per_1m_input`, `usd_saved`
- `summary` adds `usd_saved`, `by_tool`, `by_model`

- [ ] **Step 1: Add failing tests**

```python
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
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement store aggregates + service snapshot**

`by_model.model_source_dominant`: mode count; ties broken inferred > default > unknown. Sort breakdowns by `tokens_saved` desc. Legacy missing fields → `usd_saved=0`, `model_id=""`.

In `_record`, call `resolve_model` + `rate_for_model` + `compute_usd_saved`. Construct ImpactService with `cfg.impact.default_model` / `pricing_overrides`. On settings PATCH, refresh those fields (same path as `set_enabled`).

- [ ] **Step 4: Run tests — expect PASS**

Run: `cd services/core && ../../venv/bin/pytest tests/test_impact.py tests/test_impact_pricing.py -v`

- [ ] **Step 5: Commit only if user asked**

---

### Task 4: HTTP `/impact/pricing` + header probe + MCP bridge

**Files:**
- Modify: `services/core/src/mycelium/adapters/http/app.py`
- Modify: `services/core/src/mycelium/bridges/mcp/client.py`
- Modify: `services/core/src/mycelium/bridges/mcp/server.py`
- Modify: `services/core/tests/test_impact.py`

**Interfaces:**
- `GET /impact/pricing` → `{ default_model, rates: [{id, usd_per_1m_input, overridden}], disclaimer }`
- Probe from `X-Mycelium-Model-Id` (+ optional `X-Mycelium-Model-Probe`)
- MCP sets header when `_meta` has a model key

- [ ] **Step 1: Failing HTTP test**

```python
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
```

- [ ] **Step 2: Implement endpoint + `_impact_probe(request)` + pass `probe=` into record methods**

- [ ] **Step 3: MCP best-effort headers** — if FastMCP context unavailable, return `{}` (Settings default still works). Document in MCP README.

- [ ] **Step 4: Run pytest — expect PASS**

- [ ] **Step 5: Commit only if user asked**

---

### Task 5: Desktop API client + Impact page UI

**Files:**
- Modify: `apps/desktop/src/api/client.ts`
- Modify: `apps/desktop/src/pages/ImpactPage.tsx`

- [ ] **Step 1: Extend types** — `usd_saved`, `by_tool`, `by_model` on summary; model/$ on events; `getImpactPricing()`; settings fields `impact_default_model`, `impact_pricing_overrides`

- [ ] **Step 2: ImpactPage UI**
  - Hero 4 cards: Tokens saved · **$ saved** · Savings % · Recalls
  - `formatUsd` with currency USD (2–4 fraction digits)
  - Sections **Where** (`by_tool`) and **Which LLM** (`by_model`)
  - Badge: inferred→Inferred, default→Assumed, else Unknown
  - Event rows include tokens, $, model, badge
  - Spec disclaimer text
  - Guard missing fields for older Core (`?? 0` / `?? []`)

- [ ] **Step 3: Manual dogfood** — Search once, open `/impact`, expect Assumed + $ if default has a rate

- [ ] **Step 4: Commit only if user asked**

---

### Task 6: Settings UI — default model + rate editor

**Files:**
- Modify: `apps/desktop/src/pages/SettingsPage.tsx`
- Modify: `apps/desktop/src/api/client.ts` if save payload needs typing

- [ ] **Step 1: Load `getImpactPricing()` with settings**

- [ ] **Step 2: UI under Impact toggle**
  - Default model `<select>`
  - Rate rows: id + `$ / 1M input` number inputs
  - **Save:** PATCH `impact_default_model` + `impact_pricing_overrides` = full draft map (all shown rates → number). Harmless when equal to shipped defaults.
  - **Reset:** PATCH `impact_pricing_overrides: {}` and `impact_default_model: "claude-sonnet-4"`, then reload pricing

- [ ] **Step 3: Manual check** — set `gpt-4o` @ `$1/1M`, Search, confirm new events

- [ ] **Step 4: Commit only if user asked**

---

### Task 7: Docs

**Files:**
- Modify: `docs/POSITIONING.md`
- Modify: `services/core/src/mycelium/bridges/mcp/README.md`
- Modify: `docs/superpowers/specs/2026-07-27-impact-cost-estimates-design.md` (status → Implemented after code lands)

- [ ] **Step 1:** POSITIONING Numbers row for live estimated $ saved (Desktop Impact; editable rates; not Cursor billing)

- [ ] **Step 2:** MCP README note on `X-Mycelium-Model-Id` + Cursor usually missing model

- [ ] **Step 3:** Flip spec status after implementation complete

- [ ] **Step 4: Commit only if user asked**

---

## Spec coverage

| Spec requirement | Task |
|---|---|
| Snapshot model + rate + usd on events | 3 |
| resolve inferred → default → unknown | 1, 3, 4 |
| Pricing table + overrides | 1, 2, 6 |
| Summary usd + by_tool + by_model | 3 |
| GET `/impact/pricing` | 4 |
| Settings default model + rates | 2, 6 |
| Impact UI where / LLM / $ | 5 |
| Honest disclaimers | 5, 7 |
| MCP best-effort probe | 4 |
| Legacy events usd=0 | 3 |
| No marketing site sync | Global Constraints |

## Self-review notes

- No TBD placeholders
- Names locked: `model_id`, `model_source`, `usd_per_1m_input`, `usd_saved`, `impact_default_model`, `impact_pricing_overrides`, header `X-Mycelium-Model-Id`, default model `claude-sonnet-4`
