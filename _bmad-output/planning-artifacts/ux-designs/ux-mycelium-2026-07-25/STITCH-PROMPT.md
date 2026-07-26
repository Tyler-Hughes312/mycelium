# STITCH PROMPT — Mycelium (paste into Google Stitch)

**Tool:** https://stitch.withgoogle.com  
**Afterward:** download/export screens + any DESIGN.md/HTML into:
`_bmad-output/planning-artifacts/ux-designs/ux-mycelium-2026-07-25/imports/`

---

Design a **local-first developer desktop application** called **Mycelium**, plus a matching **narrow VS Code side panel**. This is a real product UI for AI-heavy engineers (Cursor / Claude Code users), not a marketing landing page and not a SaaS admin dashboard.

## Product in one sentence
Mycelium auto-builds a knowledge graph from a developer’s git history and code, runs **local RAG/embeddings**, and includes an **Obsidian-style markdown thinking vault** — then surfaces the right context in a desktop app and editor plugin. **Code never leaves the machine by default.**

## Visual direction
- **Dark-first**, calm, dense, tool-like (Linear / Raycast / Obsidian energy).
- Metaphor: **mycelium / hyphae / network** as *subtle structure* (soft branching accents, node-like chips) — **not** cartoon mushrooms.
- **Avoid:** purple gradients, cream+terracotta serif cliché, neon cyberpunk glow, glassy generic AI dashboards, emoji-heavy empty states.
- Typography: distinctive but readable sans for UI; **monospace only** for file paths and commit SHAs.
- Motion: subtle only (progress, result appear).

## Design system deliverables
Produce a cohesive system with:
- Color tokens (surface, raised, border, foreground, muted, accent, danger)
- Type ramp (display, body, label, mono)
- Radius + spacing
- Components: **result row**, **provenance chip** (Symbol / Commit / Note / File), **status pill**, **index progress**, **note editor chrome**, **backlinks list**, **empty/error states**, **left nav rail**

## Screens to generate (high fidelity)

### Desktop (macOS window)
1. **Home / Library** — list of indexed repos with health/status; prominent search entry; primary CTA “Add workspace”.
2. **Index Console** — add local git repo path; live progress (files/commits); cancel; error state example.
3. **Search / RAG results** — query field + **max ~10 ranked results**; each row has snippet + path + provenance chips; no infinite scroll spam.
4. **Vault / Note editor** — markdown note open; wikilink affordance; **backlinks** sidebar; title + path.
5. **Settings / Privacy** — vault path, embedding model, git history depth, and a clear **“Stays on this machine”** trust panel (no account signup).

### Editor plugin
6. **VS Code side panel (narrow ~340px)** — Core connection status; ranked focus context for current file; “New note” button; same tokens/components as desktop.

## UX rules to respect
- Desktop = full console (workspaces, index, search, vault, settings).
- Side panel = focus context + quick note only (not a second settings app).
- Local-only trust must be visually obvious in Settings and empty/onboarding.
- No billing, teams, cloud sync, or login screens.

## Output preference
For each screen: polished UI mock. If Stitch can emit **DESIGN.md** tokens and/or **HTML**, include those. Name screens clearly: `01-home`, `02-index`, `03-search`, `04-vault`, `05-settings`, `06-side-panel`.
