---
name: Mycelium
description: Local-first context layer for AI-heavy developers — desktop + editor plugin. Soft Electric Instrument system.
status: final
sources:
  - stitch:projects/1582993350217593804
  - docs/superpowers/specs/2026-07-25-soft-electric-ui-revamp-design.md
updated: 2026-07-25
colors:
  surface: '#111417'
  surface-raised: '#161B20'
  surface-overlay: '#1C2329'
  background: '#111417'
  foreground: '#E7ECEF'
  muted: '#8B979F'
  border: '#2A333B'
  primary: '#6EC8FF'
  accent-hypha: '#6EC8FF'
  accent-muted: '#3A7FA8'
  accent-dim: '#1A3A4D'
  accent-spore: '#E5C276'
  danger: '#C45C5C'
  secondary: '#E5C276'
typography:
  headline-lg:
    fontFamily: IBM Plex Sans
    fontSize: 28px
    fontWeight: '500'
  body-md:
    fontFamily: IBM Plex Sans
    fontSize: 14px
    fontWeight: '400'
  label-md:
    fontFamily: IBM Plex Sans
    fontSize: 12px
    fontWeight: '500'
  technical-mono:
    fontFamily: IBM Plex Mono
    fontSize: 12px
    fontWeight: '400'
rounded:
  sm: 0.375rem
  DEFAULT: 0.5rem
  md: 0.5rem
  lg: 0.5rem
  xl: 0.625rem
  full: 9999px
spacing:
  unit: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
components:
  button-primary:
    background: '{colors.primary}'
  provenance-chip:
    background: '{colors.surface-overlay}'
    border: '{colors.border}'
  status-pill-healthy:
    color: '{colors.primary}'
  result-selected:
    accent: '{colors.primary}'
---

# Mycelium — DESIGN.md

**Soft Electric Instrument** — evolved from the Stitch Organic Technical base. Stitch HTML under `mockups/` is historical until regenerated.

## Brand & Style

Mycelium is a **Soft Electric** instrument — calm, dense, local-first. Dark-first IDE energy. Soft electric light-blue accents with clean edges (almost no glow). No purple SaaS gradients, no cream terracotta, no cyberpunk bloom.

## Colors

- **Primary / accent-hypha** (`#6EC8FF`) — connected, healthy, primary actions, selection/focus
- **Accent muted** (`#3A7FA8`) — primary containers / pressed fills
- **Accent dim** (`#1A3A4D`) — selected row wash
- **Secondary / accent-spore** (`#E5C276`) — indexing / warn only (not selection)
- **Surfaces** — tonal layers (`surface` → `surface-raised` → `surface-overlay`), prefer borders over shadows
- **Danger** — errors only

## Typography

IBM Plex Sans for UI. **IBM Plex Mono only** for paths, SHAs, and logs.

## Layout & Spacing

4px base unit. Left nav rail (~176px) + main content (+ optional meta/backlinks). Calm density; compact rows. Inputs/rows ~8px radius; primary buttons ~10px.

## Components

Result rows, provenance chips (Symbol / Commit / Note / File), status pills, index progress, note editor, backlinks list, trust panel, narrow editor side panel.

## Do's and Don'ts

**Do:** typed provenance, local-only trust cues, ≤10 ranked results, blue selection.  
**Don't:** account walls, billing, infinite scroll spam, decorative fungi, purple AI marketing UI, gold selection glow.

## Screens

See `imports/` and `SCREEN-INDEX.md`. Live Stitch project (historical): https://stitch.withgoogle.com/projects/1582993350217593804
