# Impact Cost Estimates ($ + Model Attribution) — Design Spec

**Date:** 2026-07-27  
**Status:** Implemented — plan at `docs/superpowers/plans/2026-07-27-impact-cost-estimates.md`  
**Product:** [Mycelium](https://github.com/Tyler-Hughes312/mycelium) — local-first codebase context layer  
**Related:** `docs/superpowers/specs/2026-07-26-impact-metrics-design.md` (Phase 2 token telemetry)  
**Positioning:** `docs/POSITIONING.md`

## Goal

Extend Desktop **Impact** so each Mycelium recall (Search / Focus / Vault pack via Desktop or MCP) shows:

1. **Where** tokens were saved (by tool)
2. **Which LLM** the avoided context would have billed against (best-effort inference + Settings default)
3. **Money saved** using editable API list prices (`$ / 1M input tokens`)

**Audience:** Developers dogfooding Mycelium who want a concrete before/after vs dumping matched files into Cursor/Claude.

**Success:** After MCP Search/Focus usage, Impact shows tokens + $ with model labels that honestly say *inferred*, *assumed (default)*, or *unknown* — never pretend Cursor subscription invoices were read.

## Constraints (locked)

| Constraint | Choice |
|---|---|
| Without-Mycelium baseline | **A** — dump matched file bodies (existing `estimate_query_impact` / pack ceiling math) |
| $ formula | `usd_saved = tokens_saved / 1_000_000 * usd_per_1m_input` |
| Pricing | **C** — ship curated model rate table + Settings overrides |
| Model identity | **Try C** — probe MCP `_meta` / headers / client extras; **fallback** Settings `impact_default_model` |
| Storage | Local only under `~/.mycelium`; no cloud telemetry |
| Honesty | Always label estimates; never claim LLM billing accuracy or Cursor plan pricing |

### Reality check on Cursor model inference

As of this design, Cursor’s external MCP path does **not** reliably send the active chat model id to tool servers (community reports: even `composerId` is dropped from `_meta`). Therefore:

- Inference is **best-effort** and expected to miss often in v1.
- Impact UI **must** show Assumed/Unknown clearly.
- Resolution order is still implemented so we upgrade automatically if Cursor (or another MCP host) starts sending model metadata.

## Approach (locked)

**Approach 2 — Snapshot rate + model on each event**

Extend existing Impact events at record time with model + rate snapshot + `usd_saved`. Summary aggregates tokens and dollars. Changing rates later does not rewrite historical `$`.

**Not chosen:** Recompute $ only at read time (history jumps) · Separate cost-audit module (overkill).

## Event schema (extends Phase 2)

Existing fields remain required. New fields:

| Field | Type | Meaning |
|---|---|---|
| `model_id` | string | e.g. `claude-sonnet-4`, `gpt-4o`, or `""` if unknown |
| `model_source` | enum | `inferred` \| `default` \| `unknown` |
| `usd_per_1m_input` | number | Rate snapshot used for this event (0 if unknown model / no rate) |
| `usd_saved` | number | `tokens_saved / 1e6 * usd_per_1m_input` |

Backward compatible: old events without these fields treat missing as `model_source=unknown`, `usd_saved=0`.

## Model resolution

```text
1. Probe MCP request context for model hints
   (_meta keys, headers, FastMCP request context extras — whatever is present)
2. Else Settings.impact_default_model (if set)
3. Else model_id="" and model_source=unknown
```

Desktop HTTP recall paths (Search from UI) use Settings default only (no MCP meta) → usually `default`.

Store raw probe keys that matched (optional debug field `model_probe` string, truncated) — **no prompt text**.

## Pricing table

- Shipped defaults in Core (small curated list: Claude Sonnet / Opus / Haiku class, GPT-4o / 4.1 class, Gemini Flash / Pro class — exact ids + rates chosen at implementation from public list prices, documented in Settings UI as “API list price estimates”).
- User overrides persisted in `config.toml` / settings JSON under `~/.mycelium`.
- Settings: pick default model; edit `$ / 1M input`; reset to shipped defaults.
- Output-token pricing: **out of scope** (savings are context/input avoidance).

## Core API changes

| Method | Path | Change |
|---|---|---|
| GET | `/impact/summary?range=` | Add `usd_saved`; add `by_tool[]` and `by_model[]` aggregates |
| GET | `/impact/events` | Return new event fields |
| GET | `/impact/pricing` | Return default model + rate table (effective rates after overrides) |
| PATCH | `/settings` | Accept `impact_default_model`, `impact_pricing_overrides` |
| DELETE | `/impact/events` | Unchanged |

`by_tool` / `by_model` shape (summary):

```json
{
  "by_tool": [
    { "tool": "search", "event_count": 12, "tokens_saved": 80000, "usd_saved": 0.24 }
  ],
  "by_model": [
    {
      "model_id": "claude-sonnet-4",
      "model_source_dominant": "default",
      "event_count": 12,
      "tokens_saved": 80000,
      "usd_saved": 0.24
    }
  ]
}
```

Instrument once in `ImpactService._record` so Desktop HTTP and MCP share the same counters.

## Desktop UI

### Impact page

- Hero: tokens saved, **$ saved**, savings %, recall count (range tabs unchanged).
- Section **Where:** table/bars by tool.
- Section **Which LLM:** by `model_id` + source badge.
- **Recent events:** time, tool, workspace, served/baseline/saved tokens, model + badge, $ saved.
- Persistent disclaimer (exact intent):

> Estimated vs dumping matched files into the model context. Uses API list prices you can edit in Settings — not Cursor subscription billing. When Cursor does not send a model id, Mycelium uses your Impact default model and labels it Assumed.

### Settings

- Impact tracking toggle + clear (existing).
- Default model picker (from rate table).
- Editable rate rows; reset defaults.

## Tests

- Unit: `usd_saved` math; resolution order inferred > default > unknown; overrides beat shipped rates; old events aggregate with `usd_saved=0`.
- Summary: `by_tool` / `by_model` totals match event sum.
- UI: types + render populated/empty; Assumed badge when `model_source=default`.

## Out of scope

- Marketing site live $ figures.
- Output-token / full-request cost modeling.
- Reading Cursor invoices or plan quotas.
- Cross-machine sync.
- Guaranteeing model inference from Cursor (best-effort only).

## Implementation order

1. Pricing config + Settings API  
2. Extend `ImpactService` / store / summary aggregates + MCP meta probe  
3. Desktop Impact + Settings UI  
4. Tests + dogfood via MCP Search  

## Open decisions resolved

| Decision | Choice |
|---|---|
| Model attribution | Try infer + Settings default fallback |
| Pricing | Table + overrides |
| Baseline | Dump matched files (existing) |
| $ timing | Snapshot on event (Approach 2) |
| Token side | Input list price only |
