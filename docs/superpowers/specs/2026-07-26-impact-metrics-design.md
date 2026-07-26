# Impact Metrics — Design Spec

**Date:** 2026-07-26  
**Status:** Phase 1 plan at `docs/superpowers/plans/2026-07-26-impact-metrics-web.md` — Phase 2 Desktop telemetry still follow-up  
**Product:** [Mycelium](https://github.com/Tyler-Hughes312/mycelium) — local-first context layer  
**Related:** `docs/superpowers/specs/2026-07-26-mycelium-marketing-site-design.md`

## Goal

1. **Phase 1 (web, ship first):** Replace the marketing site’s `#download` (GetIt) chapter with an **Impact** section that explains token savings and how Mycelium improves day-to-day codebase work — using labeled illustrative metrics.
2. **Phase 2 (follow-up):** Add **live, local-only impact tracking** in Core + a Desktop **Impact** page that shows real savings from recall/MCP usage.

**Audience:** AI-heavy developers evaluating Mycelium; existing Desktop users who want proof of token savings.

**Success:** Visitors understand *how many tokens this would save* and *why the codebase gets better* without leaving the marketing scroll. Desktop users later see live counters that match that story, without any cloud telemetry.

## Approach (locked)

**Approach 1 — Impact strip + benefit stories**, then Desktop telemetry.

- Marketing: 3–4 big illustrative stats + short “codebase better” lines + honest disclaimer.
- Desktop follow-up: Core records served vs baseline token estimates; Desktop Impact page aggregates today / week / all-time.

**Not chosen:** Interactive savings calculator (Approach 2) · Narrative-only with no big numbers (Approach 3).

**Download CTA placement (locked):** Compact Download remains in **nav** (external Releases) and at the **end of Setup**. Impact has **no** download CTA.

## Phase 1 — Marketing Impact (implement now)

### Page architecture changes

| Before | After |
|--------|-------|
| Nav: Features · Why · Setup · Download | Nav: Features · Why · Setup · **Impact** · Download (Download → `LINKS.releases`) |
| Chapters: Hero → Outcomes → Capabilities → Setup → **GetIt** → Footer | Hero → Outcomes → Capabilities → Setup → **Impact** → Footer |

- Remove `apps/web/src/components/GetIt.tsx` (or stop importing it; prefer delete if unused).
- Add `apps/web/src/components/Impact.tsx`.
- Update `App.tsx`, `SiteNav.tsx`, `content.ts`, `content.test.mjs`.
- Setup footer: add primary **Download Desktop** button (Releases) beside existing install-guide link.
- Scroll theater: GetIt is not pinned today; Impact needs **no new pin** (stay within ≤2 pins). No GSAP chapter required beyond existing patterns unless a light fade-in is already used elsewhere.

### Content (locked direction)

Copy lives in `apps/web/src/content.ts` as `IMPACT_INTRO` + `IMPACT_METRICS[]`.

**Intro**

- Eyebrow: `Impact`
- Headline: `Fewer tokens. Sharper code. Same machine.`
- Sub: One sentence on retrieving slices instead of pasting haystacks (align tone with Outcomes).

**Four metric cards**

| id | Stat (display) | Title / benefit angle | Body (why codebase / workflow gets better) |
|----|----------------|------------------------|-----------------------------------------------|
| `tokens` | `~60–90%` | Fewer context tokens | Focus/search packets vs dumping whole files — spend window on the answer, not the haystack. |
| `packet` | `1 packet` | Per question | Symbols + commits + notes that match — not half the repo in every chat. |
| `reuse` | `Library-wide` | Reuse without re-paste | Find the auth helper / fixture / ADR you already wrote in another imported repo. |
| `grounded` | `Your patterns` | Grounded outputs | Answers match naming, error handling, and decisions you already shipped. |

Exact display strings may be tuned in implementation as long as the four ids and the illustrative disclaimer remain.

**Disclaimer (required)**

> Illustrative of typical sessions — your Desktop app will track live savings once telemetry ships.

### Visual / layout

- Match Outcomes / Setup: slate bg, teal accents, Space Grotesk display, DM Sans body.
- Prefer a responsive grid (2×2 on desktop, stack on mobile) or a clean metric row + short bodies — **not** a dense dashboard and **not** a card-farm of unrelated CTAs.
- No hero overlays, no download CTA inside Impact.
- Optional soft radial wash consistent with Outcomes (teal / violet) — keep atmosphere, avoid purple-on-white AI defaults.

### Error / edge handling (web)

- Static content only; no runtime data fetch.
- External Download links use `target="_blank"` + `rel="noreferrer"` (existing pattern).

### Phase 1 tests

- Extend `content.test.mjs`: IMPACT has four ids; blob mentions token/savings theme; disclaimer contains `illustrative` (case-insensitive).
- Existing CTA URL tests remain; Setup still must not mention shell installers.
- Manual: nav Impact scrolls to `#impact`; Download opens Releases; Setup shows Download button.

### Phase 1 out of scope

- Real measured numbers on the site.
- Desktop / Core changes.
- Cloud analytics.

---

## Phase 2 — Live Desktop telemetry (follow-up)

### Privacy (non-negotiable)

- Storage under `~/.mycelium` only.
- **No** cloud export, product analytics vendor, or phone-home.
- Settings toggle: `impact_tracking_enabled` (default **on**).
- User can clear all impact events.
- Events store **counts and metadata only** — no prompt text, no file body contents.

### What gets recorded

On each successful recall path used by agents/UI (at minimum):

- MCP / HTTP: `search`, `focus`, `vault_pack` (and equivalents already exposed)

Per event:

| Field | Meaning |
|-------|---------|
| `ts` | ISO timestamp |
| `tool` | e.g. `search`, `focus`, `vault_pack` |
| `workspace_id` | Optional workspace id |
| `served_tokens` | Estimated tokens actually returned in the response / pack |
| `baseline_tokens` | Estimated “naive paste” baseline (see math below) |
| `tokens_saved` | `max(0, baseline_tokens - served_tokens)` |

### Baseline math (honest, labeled)

- Prefer a **local, deterministic estimate** (e.g. character count / 4, or existing `tokens_est` helpers on pack responses).
- **Baseline:** rough size of what a developer might have pasted instead (matched file bodies, or pack/max ceiling when files aren’t fully loaded) — implementation picks one rule and documents it in API/UI copy.
- UI always labels savings as **estimated** (“vs dumping matched files” / similar). Never claim LLM-billed token accuracy.

### Core APIs

| Method | Path | Behavior |
|--------|------|----------|
| GET | `/impact/summary?range=today\|week\|all` | Aggregates: `tokens_saved`, `served_tokens`, `baseline_tokens`, `event_count`, derived `savings_pct` |
| GET | `/impact/events?limit=` | Recent events (newest first) |
| DELETE | `/impact/events` | Wipe all impact events |
| — | Settings / config | `impact_tracking_enabled`; when false, recall paths skip append |

Instrument recall handlers once; Desktop and MCP share the same Core counters.

### Desktop UI

- New nav item **Impact** between Search and Vault (`/impact`).
- Page shows: today / week / all-time tokens saved, savings %, recall count; short “why this helps” copy; recent events list; link to Settings for toggle + clear.
- Empty state: explain that using Search / MCP will populate metrics.
- Respect toggle: if disabled, show pause messaging + enable CTA.

### Phase 2 tests

- Core unit tests: savings clamp, range aggregation, disabled tracking writes nothing, delete clears store.
- Desktop: client types + empty/populated summary rendering (lightweight).

### Phase 2 out of scope

- Syncing Desktop numbers back onto the marketing site.
- Per-model cost ($) estimates.
- Cross-machine sync.

---

## Implementation order

1. Phase 1 web Impact (this plan’s first implementation cycle).
2. Separate plan + implementation for Phase 2 Core store → APIs → Desktop page.

## Open decisions resolved

| Decision | Choice |
|----------|--------|
| Scope | Both marketing Impact + Desktop telemetry |
| Phasing | Web Impact first; telemetry follow-up |
| Replace | GetIt / `#download` chapter → Impact |
| Download CTA | Nav + Setup footer (not inside Impact) |
| Approach | Impact strip + benefit stories |

## Non-goals

- Inventing fake “customer case study” numbers without the illustrative label.
- Shipping Phase 2 in the same PR as Phase 1 unless explicitly requested later.
