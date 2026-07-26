# Soft Electric UI Revamp — Design Spec

**Date:** 2026-07-25  
**Product:** Mycelium desktop (`apps/desktop`) + shared UI tokens (`packages/ui`)  
**Status:** Approved for planning (visual direction + shell/surfaces)

## Problem

The current Stitch-backed **Organic Technical** UI (sage/hypha green, flat dense chrome) reads as archaic — utilitarian but dated. Goal: modernize the desktop shell and all primary surfaces without changing product IA or adding screens.

## Decisions (locked)

| Decision | Choice |
|---|---|
| Scope | Full modernization of shell + Library, Search, Index, Vault, Settings |
| Accent | Soft electric neon **light blue** fully **replaces** hypha green |
| Neon intensity | Soft electric — clean edges, **almost no glow** |
| Approach | Same screens/IA; restyle tokens + AppShell + all pages |
| Out of scope | New screens, graph explorer, light mode, Stitch HTML mockup rewrite, editor side panel (unless token inheritance is free) |

## Visual identity

**Name:** Soft Electric Instrument  
**Feel:** Dark-first, dense, calm developer tool (Linear / Raycast energy). Local-first trust cues preserved. Borders over shadows. No purple SaaS gradients, no cream/terracotta, no cyberpunk bloom.

### Color tokens

| Role | Hex | Notes |
|---|---|---|
| Accent / primary | `#6EC8FF` | CTAs, active nav, healthy/connected, wikilinks |
| Accent muted | `#3A7FA8` | Primary container / pressed fills |
| Accent dim | `#1A3A4D` | Selected row tint, low-opacity focus wash |
| Surface lowest | `#0B0E11` | Rail background |
| Surface | `#111417` | Main canvas |
| Surface raised | `#161B20` | Cards / rows |
| Surface overlay | `#1C2329` | Inputs / elevated panels |
| Foreground | `#E7ECEF` | Primary text |
| Muted | `#8B979F` | Secondary text |
| Border | `#2A333B` | Dividers, default borders |
| Secondary (warn) | `#E5C276` | Indexing / in-progress only |
| Danger | `#C45C5C` | Errors only |

**Migration rule:** Every former `#9cd2ba` / `accent-hypha` / `primary` green maps to `#6EC8FF` (or muted/dim variants for containers). Spore/gold stays for non-healthy status only — not as selection accent. Selection/focus uses blue (`accent-dim` tint or `#6EC8FF` border), not gold.

### Typography

- Keep **IBM Plex Sans** (UI) and **IBM Plex Mono** (paths, SHAs, logs only).
- Page titles: medium weight, slight negative tracking (−0.01em).
- Do not use mono for nav labels or body copy.

### Shape & motion

- Inputs / list rows: `8px` radius  
- Primary buttons: `10px` radius  
- Status pills / chips: full / `9999px` or `6px` (keep compact)  
- Motion: ~150ms color/border transitions; no box-shadow glow; indexing may keep a subtle pulse on the status dot only

## Shell

**Rail (~176px)**
- Brand: node glyph + “Mycelium” / “Local Instrument”
- CTA: primary blue solid fill (“New note” preferred label; “New Node” acceptable if already wired)
- Active nav: 2px left bar in `#6EC8FF` + `accent-dim` background tint; not bold green wash
- Footer Docs / Update: muted, unchanged behavior

**Top bar**
- Keep “Local Only” + Core status pill (connected = blue dot)
- Remove decorative avatar if it is non-functional
- Hub / terminal icons: keep only if they map to real actions; otherwise drop in this pass

## Shared page patterns

- Title row + one primary action; hairline under title
- Search/filter: larger hit area, `8px` radius, blue border on focus (no glow)
- List rows: denser vertical rhythm; left status hairline (blue / gold / muted); hover raises surface, not a heavy border flash
- Provenance chips: neutral surface + border; type label only — accent blue reserved for selected/focus states
- Empty/error: one sentence + one action; danger color for errors only

## Per-screen polish (layout preserved)

| Screen | Changes |
|---|---|
| Library | Filter + workspace rows; tighter stats columns; healthy = blue |
| Search | Query field as focal control; ≤10 results; selected row uses blue accent, not gold |
| Index | Progress fill = blue; cancel remains obvious |
| Vault | Editor + backlinks chrome; `[[wikilink]]` color = primary blue |
| Settings | Trust panel copy unchanged; controls use new accent |

## Implementation surfaces

1. `packages/ui/src/theme.css` — update shared CSS variable **values** (keep names like `--mycelium-primary` / `--mycelium-accent-hypha` for less churn; both resolve to soft electric blue)  
2. `apps/desktop/src/index.css` — Tailwind `@theme` primary/accent tokens + radius tweaks (`8px` rows/inputs, `10px` primary buttons)  
3. `apps/desktop/src/components/AppShell.tsx` — rail ~176px, active states, CTA, header cleanup  
4. Pages: `LibraryPage`, `SearchPage`, `IndexPage`, `VaultPage`, `SettingsPage` — class/token alignment, selection accent, density  
5. Shared components in `@mycelium/ui` that hardcode green hex (e.g. `StatusPill`, chips) — use tokens only  
6. Update `_bmad-output/planning-artifacts/ux-designs/ux-mycelium-2026-07-25/DESIGN.md` color table to Soft Electric (docs sync; Stitch HTML mockups left as historical)

## Non-goals

- Redesigning information architecture or navigation model  
- Force-directed graph as primary nav  
- Account / billing / onboarding walls  
- Full Stitch re-export or PNG mockup regeneration (optional follow-up)  
- Light theme

## Success criteria

- No sage/hypha green remains as a primary interactive or “healthy” accent in the desktop app  
- Shell and all five pages feel like one modern system (consistent radius, blue accent, density)  
- Still readable as a local-first developer instrument — not a marketing landing page or neon HUD  
- Reduced-motion: no required glow animations (none introduced)

## Open follow-ups (not blocking)

- VS Code/Cursor side panel visual sync (inherits `@mycelium/ui` tokens if it consumes them)  
- Optional Stitch project refresh for design-source truth  
- Git init / commit of this spec (workspace is not currently a git repository)
