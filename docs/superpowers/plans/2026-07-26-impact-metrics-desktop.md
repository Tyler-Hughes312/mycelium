# Impact Metrics (Phase 2 — Desktop Telemetry) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record local-only token-savings estimates on Core recall paths (`/query`, `/context/focus`, `/vault/pack`) and show live Impact metrics in the Desktop app.

**Architecture:** New `ImpactStore` JSON file under `~/.mycelium/data/impact_events.json`. A small `impact_service` records events after successful recall. HTTP handlers instrument once (MCP uses the same Core HTTP/domain paths). Desktop adds `/impact` page + Settings toggle via existing `/settings` PATCH.

**Tech Stack:** Python 3 / FastAPI Core, pytest (`services/core/tests`), React + TypeScript Desktop (`apps/desktop`), Vite.

**Spec:** `docs/superpowers/specs/2026-07-26-impact-metrics-design.md` (Phase 2 section)

## Global Constraints

- Local-only under `~/.mycelium` — no cloud export / analytics vendor
- Events: counts + metadata only (no prompt text, no file bodies in the store)
- `impact_tracking_enabled` default **on**; when false, recall paths skip append
- Token math uses existing `estimate_tokens` (char/4) — UI labels **estimated**
- Baseline rule (locked):
  - **vault_pack:** `baseline = max(max_tokens, served)` where `served = pack["tokens_est"]`
  - **query / focus:** `served = estimate_tokens(concatenated result snippets/texts)`; `baseline = max(served, sum of on-disk file sizes for unique result paths capped at 200_000 chars each, estimated via estimate_tokens)` — if no readable paths, `baseline = max(served * 4, served)`
  - `tokens_saved = max(0, baseline - served)`
- Skip git commits unless the user asks
- Do not sync Desktop numbers back to the marketing site

---

## File map

| File | Responsibility |
|------|----------------|
| `services/core/src/mycelium/adapters/store/impact_store.py` | Append/list/clear/summarize JSON events |
| `services/core/src/mycelium/core/domain/impact_service.py` | Record helpers + baseline math; respects config flag |
| `services/core/tests/test_impact.py` | Unit tests for math, ranges, disable, clear |
| `services/core/src/mycelium/core/config.py` | `impact_tracking_enabled` in TOML + settings_dict/update_config |
| `services/core/src/mycelium/adapters/http/app.py` | Instrument query/focus/pack; GET/DELETE impact; settings field |
| `apps/desktop/src/api/client.ts` | Types + `getImpactSummary`, `getImpactEvents`, `clearImpactEvents`, settings field |
| `apps/desktop/src/pages/ImpactPage.tsx` | Live Impact UI |
| `apps/desktop/src/App.tsx` | Route `/impact` |
| `apps/desktop/src/components/AppShell.tsx` | Nav item between Search and Vault |
| `apps/desktop/src/pages/SettingsPage.tsx` | Toggle + clear button |

---

### Task 1: Impact store + service + tests (TDD)

**Files:**
- Create: `services/core/src/mycelium/adapters/store/impact_store.py`
- Create: `services/core/src/mycelium/core/domain/impact_service.py`
- Create: `services/core/tests/test_impact.py`
- Modify: `services/core/src/mycelium/adapters/store/__init__.py` (export if other stores are exported)

**Interfaces:**
- Consumes: `estimate_tokens` from `mycelium.core.domain.vault_service`; `read_json_object` / `write_json_atomic` from `json_io`
- Produces:
  - `ImpactEvent` TypedDict / dataclass with fields: `ts`, `tool`, `workspace_id`, `served_tokens`, `baseline_tokens`, `tokens_saved`
  - `ImpactStore(path: Path)` with `append`, `list_events(limit)`, `clear`, `summary(range: Literal["today","week","all"])`
  - `ImpactService.record_pack(...)`, `record_query(...)`, `record_focus(...)` — no-ops when `enabled=False`

- [ ] **Step 1: Write failing tests**

Create `services/core/tests/test_impact.py`:

```python
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from mycelium.adapters.store.impact_store import ImpactStore
from mycelium.core.domain.impact_service import (
    compute_tokens_saved,
    estimate_query_impact,
    estimate_pack_impact,
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
```

- [ ] **Step 2: Run tests — expect fail**

```bash
cd services/core && python -m pytest tests/test_impact.py -v
```

Expected: FAIL (modules missing).

- [ ] **Step 3: Implement store**

Create `services/core/src/mycelium/adapters/store/impact_store.py`:

```python
"""Local impact event log under ~/.mycelium/data (counts only)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

from mycelium.adapters.store.json_io import read_json_object, write_json_atomic

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
        write_json_atomic(self.path, {"events": events})

    def append(self, event: dict[str, Any]) -> None:
        events = self._load()
        events.append(event)
        # Cap growth
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
```

Confirm `write_json_atomic` exists in `json_io.py`; if the helper has a different name, use the existing atomic write function.

- [ ] **Step 4: Implement impact_service math + record API**

Create `services/core/src/mycelium/core/domain/impact_service.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mycelium.adapters.store.impact_store import ImpactStore
from mycelium.core.domain.vault_service import estimate_tokens

_MAX_FILE_CHARS = 200_000


def compute_tokens_saved(*, served: int, baseline: int) -> int:
    return max(0, int(baseline) - int(served))


def estimate_pack_impact(*, tokens_est: int, max_tokens: int) -> tuple[int, int, int]:
    served = max(0, int(tokens_est))
    baseline = max(int(max_tokens), served)
    return served, baseline, compute_tokens_saved(served=served, baseline=baseline)


def estimate_query_impact(
    *,
    snippets: list[str],
    path_texts: dict[str, str],
) -> tuple[int, int, int]:
    served = estimate_tokens("\n".join(snippets)) if snippets else 0
    if path_texts:
        baseline = estimate_tokens(
            "\n".join(t[:_MAX_FILE_CHARS] for t in path_texts.values())
        )
        baseline = max(baseline, served)
    else:
        baseline = max(served * 4, served)
    return served, baseline, compute_tokens_saved(served=served, baseline=baseline)


class ImpactService:
    def __init__(self, store: ImpactStore, *, enabled: bool = True) -> None:
        self.store = store
        self.enabled = enabled

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def _record(
        self,
        *,
        tool: str,
        workspace_id: str | None,
        served: int,
        baseline: int,
        saved: int,
    ) -> None:
        if not self.enabled:
            return
        self.store.append(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "tool": tool,
                "workspace_id": workspace_id or "",
                "served_tokens": served,
                "baseline_tokens": baseline,
                "tokens_saved": saved,
            }
        )

    def record_pack(
        self,
        *,
        pack: dict[str, Any],
        max_tokens: int,
        workspace_id: str | None = None,
    ) -> None:
        served, baseline, saved = estimate_pack_impact(
            tokens_est=int(pack.get("tokens_est") or 0),
            max_tokens=max_tokens,
        )
        self._record(
            tool="vault_pack",
            workspace_id=workspace_id,
            served=served,
            baseline=baseline,
            saved=saved,
        )

    def record_search_or_focus(
        self,
        *,
        tool: str,
        payload: dict[str, Any],
        workspace_root: Path | None = None,
    ) -> None:
        results = payload.get("results") or []
        snippets: list[str] = []
        path_texts: dict[str, str] = {}
        for row in results:
            if not isinstance(row, dict):
                continue
            snip = str(row.get("snippet") or row.get("text") or "")
            if snip:
                snippets.append(snip)
            path = str(row.get("path") or row.get("file_path") or "")
            if path and workspace_root is not None and path not in path_texts:
                fp = Path(path)
                if not fp.is_absolute():
                    fp = workspace_root / path
                try:
                    if fp.is_file():
                        path_texts[path] = fp.read_text(encoding="utf-8", errors="ignore")[
                            :_MAX_FILE_CHARS
                        ]
                except OSError:
                    pass
        served, baseline, saved = estimate_query_impact(
            snippets=snippets, path_texts=path_texts
        )
        self._record(
            tool=tool,
            workspace_id=str(payload.get("workspace_id") or ""),
            served=served,
            baseline=baseline,
            saved=saved,
        )
```

- [ ] **Step 5: Run tests — expect pass**

```bash
cd services/core && python -m pytest tests/test_impact.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit (only if user asked)**

---

### Task 2: Config flag + HTTP APIs + instrumentation

**Files:**
- Modify: `services/core/src/mycelium/core/config.py`
- Modify: `services/core/src/mycelium/adapters/http/app.py`
- Modify: `services/core/tests/test_impact.py` (add API integration tests with TestClient)

**Interfaces:**
- Consumes: `ImpactStore`, `ImpactService`
- Produces:
  - Config key `impact_tracking_enabled` (bool, default true) under `[network]` or new `[impact]` — prefer `[impact] tracking_enabled = true`
  - `GET /impact/summary?range=`
  - `GET /impact/events?limit=`
  - `DELETE /impact/events`
  - `PATCH /settings` accepts `impact_tracking_enabled`
  - After successful `/query`, `/context/focus`, `/vault/pack` → `impact_service.record_*`

- [ ] **Step 1: Extend config**

Add to `MyceliumConfig` (or nested dataclass):

```python
@dataclass(frozen=True)
class ImpactSettings:
    tracking_enabled: bool = True
```

Wire through `ensure_local_layout`, default TOML, `settings_dict`, and `update_config(..., impact_tracking_enabled: bool | None = None)`.

Expose in settings JSON as `impact_tracking_enabled: bool`.

- [ ] **Step 2: Wire ImpactService on app lifespan**

In `create_app` lifespan, after data_dir known:

```python
impact_path = cfg.paths.data_dir / "impact_events.json"
impact = ImpactService(
    ImpactStore(impact_path),
    enabled=cfg.impact.tracking_enabled,  # or wherever stored
)
application.state.impact_service = impact
```

- [ ] **Step 3: Add HTTP routes**

```python
@application.get("/impact/summary")
def impact_summary(range: str = "all") -> dict[str, Any]:
    if range not in ("today", "week", "all"):
        range = "all"
    return {"summary": application.state.impact_service.store.summary(range)}  # type: ignore[arg-type]

@application.get("/impact/events")
def impact_events(limit: int = 50) -> dict[str, Any]:
    events = application.state.impact_service.store.list_events(limit)
    return {"events": events, "count": len(events)}

@application.delete("/impact/events")
def impact_clear() -> dict[str, Any]:
    application.state.impact_service.store.clear()
    return {"cleared": True}
```

- [ ] **Step 4: Instrument recall handlers**

After successful `rag_service().query(...)` / `focus(...)` / `vault_service().pack(...)`:

```python
# query
result = rag_service().query(...)
application.state.impact_service.record_search_or_focus(tool="search", payload=result, workspace_root=...)
return result

# focus — tool="focus"
# pack —
pack = vault_service().pack(...)
application.state.impact_service.record_pack(pack=pack, max_tokens=body.max_tokens)
return {"pack": pack}
```

Resolve `workspace_root` from workspace repo when `workspace_id` is a concrete id (skip or None for `*`).

On settings PATCH when `impact_tracking_enabled` changes, call `impact_service.set_enabled(...)`.

- [ ] **Step 5: Integration tests**

Append to `test_impact.py`:

```python
def test_impact_http_records_and_respects_disable(tmp_path: Path) -> None:
    from mycelium.adapters.http.app import create_app
    from mycelium.core.config import ensure_local_layout
    from fastapi.testclient import TestClient

    cfg = ensure_local_layout(tmp_path / "home")
    # force hashing embedder like test_scaffold
    text = cfg.paths.config_file.read_text(encoding="utf-8")
    if "mycelium-hashing-v1" not in text:
        text = text.rstrip() + '\n\n[embedding]\nmodel = "mycelium-hashing-v1"\n'
        cfg.paths.config_file.write_text(text, encoding="utf-8")
        cfg = ensure_local_layout(tmp_path / "home")

    app = create_app(cfg)
    client = TestClient(app)

    pack = client.post("/vault/pack", json={"max_tokens": 500}).json()
    assert "pack" in pack
    summary = client.get("/impact/summary", params={"range": "all"}).json()["summary"]
    assert summary["event_count"] >= 1

    client.patch("/settings", json={"impact_tracking_enabled": False})
    before = client.get("/impact/summary", params={"range": "all"}).json()["summary"]["event_count"]
    client.post("/vault/pack", json={"max_tokens": 500})
    after = client.get("/impact/summary", params={"range": "all"}).json()["summary"]["event_count"]
    assert after == before

    client.delete("/impact/events")
    cleared = client.get("/impact/summary", params={"range": "all"}).json()["summary"]
    assert cleared["event_count"] == 0
```

Adapt imports to match `ensure_test_layout` from `test_scaffold` if easier (import helper).

- [ ] **Step 6: Run Core tests**

```bash
cd services/core && python -m pytest tests/test_impact.py tests/test_scaffold.py -v --tb=short
```

Expected: PASS (no regressions).

---

### Task 3: Desktop client + Impact page + Settings

**Files:**
- Modify: `apps/desktop/src/api/client.ts`
- Create: `apps/desktop/src/pages/ImpactPage.tsx`
- Modify: `apps/desktop/src/App.tsx`
- Modify: `apps/desktop/src/components/AppShell.tsx`
- Modify: `apps/desktop/src/pages/SettingsPage.tsx`

**Interfaces:**
- Consumes: `/impact/*`, `/settings`
- Produces: Nav **Impact** at `/impact`; Settings toggle + clear

- [ ] **Step 1: Client types + functions**

Add to `client.ts`:

```ts
export type ImpactSummary = {
  range: "today" | "week" | "all";
  event_count: number;
  served_tokens: number;
  baseline_tokens: number;
  tokens_saved: number;
  savings_pct: number;
};

export type ImpactEvent = {
  ts: string;
  tool: string;
  workspace_id: string;
  served_tokens: number;
  baseline_tokens: number;
  tokens_saved: number;
};

export function getImpactSummary(range: "today" | "week" | "all" = "all") {
  return request<{ summary: ImpactSummary }>(
    `/impact/summary?range=${encodeURIComponent(range)}`,
  );
}

export function getImpactEvents(limit = 50) {
  return request<{ events: ImpactEvent[]; count: number }>(
    `/impact/events?limit=${limit}`,
  );
}

export function clearImpactEvents() {
  return request<{ cleared: boolean }>("/impact/events", { method: "DELETE" });
}
```

Extend `AppSettings` + `patchSettings` input with `impact_tracking_enabled?: boolean`.

- [ ] **Step 2: ImpactPage**

Create page that:
- Loads summary for today / week / all (tabs or three counters)
- Shows `tokens_saved`, `savings_pct`, `event_count` with label “Estimated vs dumping matched files / pack ceiling”
- Short why-it-helps copy (3 bullets)
- Recent events list
- Empty state when `event_count === 0`
- If settings say tracking disabled: pause message + link to Settings
- Match existing Desktop surface styles (primary teal, muted text, rounded-xl panels like Search/Vault)

- [ ] **Step 3: Route + nav**

`App.tsx`:

```tsx
<Route path="impact" element={<ImpactPage />} />
```

`AppShell` `mainNav` insert after Search:

```ts
{ to: "/impact", label: "Impact", icon: "monitoring", end: false },
```

(Use a Material Symbols name already used elsewhere if `monitoring` missing — e.g. `insights` or `speed`.)

- [ ] **Step 4: Settings toggle + clear**

In SettingsPage privacy / local section:
- Checkbox bound to `impact_tracking_enabled` (default true when undefined)
- Include in `patchSettings` on Apply
- Button “Clear impact history” → `clearImpactEvents()` with confirm

- [ ] **Step 5: Verify Desktop build**

```bash
cd apps/desktop && npm run build
```

Expected: PASS.

---

### Task 4: Spec + plan status

**Files:**
- Modify: `docs/superpowers/specs/2026-07-26-impact-metrics-design.md`
- This plan file checkboxes as tasks complete

- [ ] **Step 1: Update design status**

```markdown
**Status:** Phase 1 shipped; Phase 2 plan at `docs/superpowers/plans/2026-07-26-impact-metrics-desktop.md`
```

- [ ] **Step 2: Manual smoke**

1. Start Core + Desktop
2. Run a vault pack or search
3. Open Impact — counters move
4. Disable tracking in Settings — counters stop growing
5. Clear history — empty state

---

## Spec coverage

| Spec item | Task |
|-----------|------|
| Local-only JSON events | Task 1 |
| Baseline math + tokens_saved clamp | Task 1 |
| Config toggle | Task 2 |
| GET summary/events, DELETE clear | Task 2 |
| Instrument search/focus/vault_pack | Task 2 |
| Desktop Impact page + nav | Task 3 |
| Settings toggle + clear | Task 3 |
| Core unit tests | Task 1–2 |

## Self-review

- Baseline rule locked and documented (no TBD).
- Names consistent: `ImpactStore`, `ImpactService`, `impact_tracking_enabled`.
- MCP covered because it hits the same Core handlers.
