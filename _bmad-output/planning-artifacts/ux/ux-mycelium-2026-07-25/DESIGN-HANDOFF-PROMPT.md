# Mycelium — Design Handoff Prompt (for external UI AI)

Paste into **Google Stitch** (https://stitch.withgoogle.com), **Figma Make**, or **Galileo**. Save outputs into:
`_bmad-output/planning-artifacts/ux/ux-mycelium-2026-07-25/imports/`

---

## Product

**Mycelium** is a local-first desktop app + VS Code/Cursor plugin for AI-heavy developers. It auto-builds a knowledge graph from git + code, runs local RAG/embeddings, and includes an Obsidian-style markdown thinking vault. Privacy: code never leaves the machine by default.

## Surfaces to design (priority order)

### 1) Desktop app (primary — full product UI)
Native desktop (macOS first). Not a marketing site. Dense, calm, tool-like — think Linear / Raycast / Obsidian, not SaaS dashboard chrome.

**Screens needed:**
1. **Home / Library** — list of indexed workspace repos, index health, quick search entry
2. **Index console** — add repo, progress, errors, cancel
3. **Search / RAG results** — query + ranked results with typed provenance chips (Symbol / Commit / Note / File), small top-k list not infinite scroll spam
4. **Note / Vault** — markdown editor, backlinks sidebar, wikilink affordances
5. **Settings / Privacy** — vault path, embedding model, history depth, explicit “local-only” trust panel

### 2) VS Code/Cursor side panel (secondary — compact)
Narrow vertical panel:
- Connection status
- Ranked context for current file/symbol
- “New note” CTA
Same visual language/tokens as Desktop (shared design system).

## Audience

Senior ICs who live in Cursor/Claude Code. Skeptical of cloud tools that read their repos. Value speed, clarity, and trust over decoration.

## Aesthetic direction (constraints)

- Avoid generic AI defaults: no purple-on-white gradients, no cream+terracotta serif cliché, no neon cyberpunk glow.
- Prefer: organic-but-technical — mycelium/network metaphor as subtle structure (branching connections, soft node accents), not literal mushroom clipart.
- Dark-friendly (devs), optional light mode.
- Typography: distinctive but readable for code-adjacent UI; monospace for paths/hashes only.
- Motion: subtle (index progress, result appear) — not playful marketing motion.

## Deliverables requested

1. Visual direction / DESIGN tokens (colors, type, radius, spacing)
2. High-fidelity mockups for the 5 desktop screens + 1 side panel
3. Component inventory: result row, provenance chip, status pill, note editor chrome, empty/error states
4. If supported: export DESIGN.md-compatible tokens or HTML mockups

## Explicit non-goals for v0 UI

- Force-directed graph explorer as primary navigation
- Team/org admin, billing, cloud sync screens
- Onboarding that requires an account
