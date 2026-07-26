---
title: Sprint Change Proposal — Desktop App in V0
status: accepted
created: 2026-07-25
updated: 2026-07-25
trigger: Stakeholder requirement — full functional desktop app + VS Code/Cursor plugin in MVP
---

# Sprint Change Proposal: Mycelium Desktop App in V0

## 1. Trigger

**Type:** New requirement / strategic scope expansion (pre-implementation).  
**Problem:** Original MVP treated the VS Code Side Panel as the only human UI, with Thinking Vault as plain files. Tyler requires a **full functional desktop app** in v0 *in addition to* the editor plugin.

## 2. Impact summary

| Artifact | Impact |
|---|---|
| PRD | Add Desktop App surface; new FRs; revise MVP in/out; new UJ |
| Architecture | New `bridges/desktop` adapter; shell choice (Tauri recommended); shared UI kit with extension webview where possible |
| Epics | New **E5b Desktop Shell** (or renumber); Editor Bridge stays; UX becomes required before UI build |
| UX | **Now required** — was optional watchout; use `bmad-ux` Design handoff to external UI AI |
| Readiness | Re-gate: blocked on UX spines + shell decision before desktop stories |

## 3. Recommended path (BMAD)

1. **This change proposal** (done) → apply PRD/architecture/epic patches  
2. Fresh chat: **`bmad-ux`** with working mode **Design handoff**  
   - BMAD assembles producer prompt + EXPERIENCE skeleton  
   - External UI AI produces visuals (see §5)  
   - Save outputs into UX workspace `imports/` / `mockups/`  
3. **`bmad-architecture` Update** after shell + UI system locked  
4. **`bmad-create-epics-and-stories` Update** (or patch epics file)  
5. Then sprint planning

## 4. Product decisions proposed

| Decision | Proposal | Status |
|---|---|---|
| Surfaces in v0 | Desktop app **and** VS Code/Cursor plugin **and** MCP | Adopt |
| Desktop shell | **Tauri 2** + React (small binary, local-first fit) vs Electron | **Needs confirm** |
| Desktop owns | Index status, workspace mgmt, Vault browse/edit, RAG search, settings/privacy | Adopt |
| Extension owns | Focus Context while coding (thin; calls same Core) | Adopt |
| Shared UI | React component library used by Tauri webview + extension webview | Adopt |
| Standalone marketing site | Still out of MVP | Adopt |

## 5. UI design AI handoff (external)

BMAD UX default producer: **Google Stitch** (`https://stitch.withgoogle.com`) — DESIGN.md + per-screen HTML.

| Tool | Best for Mycelium |
|---|---|
| **Google Stitch** | BMAD-native handoff; screens + DESIGN.md |
| **Figma Make / Figma AI** | Editable design file, iteration, design system |
| **Galileo** | Fast hi-fi screen exploration into Figma |
| **v0** | React/Tailwind implementation *after* design direction exists |

**Recommended combo:** Stitch or Galileo/Figma for **look** → BMAD `DESIGN.md` + `EXPERIENCE.md` as contract → implement in Tauri/React (optionally scaffold pieces with v0).

## 6. Rollback / risk

- Scope creep risk: desktop can swallow months. Mitigate: desktop v0 = **operator console** (index, search, vault, settings), not a full Obsidian clone.  
- Dual UI maintenance: force shared React package `@mycelium/ui`.

## 7. Approval

Treated as **accepted for planning updates** based on Tyler’s explicit v0 requirement. Shell (Tauri vs Electron) and which UI AI to run first remain open for confirm.
