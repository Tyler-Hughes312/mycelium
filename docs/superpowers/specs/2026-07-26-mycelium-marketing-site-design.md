# Mycelium Marketing Site — Design Spec

**Date:** 2026-07-26  
**Status:** Approved — implementation plan at `docs/superpowers/plans/2026-07-26-mycelium-marketing-site.md`  
**Reference:** [Wix Studio transparent-video inspiration](https://www.wix.com/studio/design/inspiration/transparentvideo)  
**Product:** [Mycelium](https://github.com/Tyler-Hughes312/mycelium) — local-first context layer

## Goal

Ship a single scroll-theater marketing site that:

1. Explains what Mycelium can do (Library → Index → Search → Vault → Agents/MCP)
2. Shows how to set it up (install script / Desktop packaged path)
3. Links Desktop download (GitHub Releases) and the GitHub repo
4. Delivers “crazy” scrub-tied scroll animation in the spirit of Wix Studio’s Design Wrap — without copying their assets

**Audience:** AI-heavy developers evaluating a local-first second brain for Cursor/Claude + Desktop.

**Success:** Landing on Vercel feels memorable in the first viewport, teaches the product in one scroll, and ends with unambiguous Download + GitHub CTAs. Motion respects `prefers-reduced-motion`.

## Approach (locked)

**A — Scroll-theater SPA** in `apps/web` (Vite + React + TypeScript + Lenis + GSAP ScrollTrigger). Deploy to Vercel as a static site (`apps/web` → `dist`).

**Not chosen:** Next.js (unnecessary weight) · Astro islands (awkward for heavy GSAP choreography).

## Visual direction (hybrid)

| Layer | Treatment |
|-------|-----------|
| Product world (Hero, Get it, Footer) | Mycelium slate `#1c1f22`, teal `#00d1b2`, raised surfaces from `packages/ui` theme; Logo E SVG |
| Chapter explosions (Capabilities, Setup) | Vivid poster panels (magenta / sage / violet washes) — Wix-Studio energy, teal as signature accent |
| Display type | Space Grotesk (marketing headlines) |
| Body type | DM Sans |
| Product chrome nods | IBM Plex Sans/Mono allowed in UI mock frames |
| Visual anchors | Real product UI (Stitch comps / desktop captures) — not abstract purple gradients as the main idea |

**Anti-patterns to avoid:** AI purple-on-white defaults · emoji-as-icons · more than two pinned sections · light-mode-first.

## Page architecture

Fixed minimal nav: logo · Features · Setup · Download · GitHub (external).

| Chapter | Mood | Purpose |
|---------|------|---------|
| **Hero** | Dark slate + teal | Brand thesis + scroll cue + dual CTAs |
| **Capabilities** | Vivid pinned chapter | Horizontal card journey scrubbed by vertical scroll |
| **Setup** | High-contrast pinned steps | Three-step path to running Mycelium |
| **Get it** | Product teal return | Desktop download + GitHub |
| **Footer** | Quiet dark | License, local-first note, secondary links |

## Motion system

- **Sitewide:** Lenis smooth scroll
- **Pins:** Capabilities + Setup only (≤2 pins)
- **Hero:** Oversized type entrance; teal hypha stroke draw-in
- **Capabilities:** Vertical scroll drives horizontal track: Library → Index → Search → Vault → Agents
- **Setup:** Steps stack/lock on scrub
- **Get it:** Sticky dual CTAs settle into view
- **Reduced motion:** Disable pins/scrubs; use opacity/transform fades only
- **Tooling:** GSAP + ScrollTrigger; `ScrollTrigger.refresh()` after fonts/images load

Signature metaphor: hyphae spreading / rewiring — motion should feel like local memory connecting, not generic “floaty cards.”

## Content (locked copy direction)

### Hero

- Brand: **Mycelium**
- Headline: Local-first context layer for AI-heavy developers
- Sub: Code + Thinking Vault stay on `127.0.0.1`. No cloud account required.
- CTAs: Download Desktop · View on GitHub

### Capabilities (cards)

1. **Library** — Import repos so Search can reuse old code across projects  
2. **Index** — Local embeddings and indexes under `~/.mycelium`  
3. **Search** — Hybrid recall over symbols, commits, files, and vault notes  
4. **Vault** — Markdown second brain with buckets and wikilinks  
5. **Agents** — MCP tools for Cursor / Claude against Core on `:8787`

### Setup

1. Clone + `./scripts/install.sh`  
2. `./scripts/dev.sh` (Core `:8787` + Desktop) — or open packaged Desktop from Releases  
3. Library → Index → Search (e.g. dogfood fixture)  

Link out to README / DESKTOP-INSTALL for Gatekeeper / SmartScreen notes.

### Get it

- Primary: **Download Desktop** → `https://github.com/Tyler-Hughes312/mycelium/releases`  
- Secondary: **GitHub** → `https://github.com/Tyler-Hughes312/mycelium`  
- Note: Packaged app bundles Core; see `docs/DESKTOP-INSTALL.md`

## Tech stack

| Piece | Choice |
|-------|--------|
| App path | `apps/web` |
| Framework | Vite + React + TypeScript |
| Motion | `gsap`, `ScrollTrigger`, `lenis` |
| Design intel | ui-ux-pro-max skill → persist `apps/web/design-system/MASTER.md` |
| Art direction | Stitch MCP (project comps for hero / capability / setup frames) |
| Brand assets | `apps/logo-E-slate-teal.svg` (+ exported Stitch/screenshots under `apps/web/public`) |

### Vercel

- Root directory: `apps/web`
- Build: `npm run build`
- Output: `dist`
- Env: none (fully static)
- Optional: `vercel.json` only if rewrites needed for SPA fallback (Vite SPA: yes, rewrite `/*` → `/index.html` if client routes exist; single-page landing may not need routes)

## Tooling workflow (implementation)

1. Persist design system via ui-ux-pro-max (`--design-system --persist --motion 9`)
2. Generate Stitch desktop screens for Hero / Capabilities strip / Setup / Download
3. Scaffold `apps/web` and implement chapters with GSAP
4. Wire CTAs to Releases + GitHub
5. Verify reduced-motion + mobile (375 / 768 / 1024 / 1440)
6. Document Vercel project settings in README snippet under `apps/web`

## Out of scope

- Transparent video asset pipeline (WebM alpha) for v1 — use CSS/SVG/GSAP hypha motion + UI comps instead; revisit if assets appear later
- Auth, analytics backends, or cloud signup
- Full docs site / blog
- VS Code marketplace install CTA (optional later; Desktop + GitHub are required)

## Acceptance criteria

- [ ] `apps/web` builds and previews locally
- [ ] Hero reads as Mycelium (logo + slate/teal), not a generic SaaS template
- [ ] Capabilities chapter communicates all five surfaces via scroll journey
- [ ] Setup chapter shows three clear steps
- [ ] Download and GitHub links work and point at the official repo/releases
- [ ] Scroll theater works on desktop; mobile degrades gracefully (fewer/no pins)
- [ ] `prefers-reduced-motion` disables scrub/pin choreography
- [ ] Deploys to Vercel from `apps/web`

## Open decisions (resolved)

| Decision | Resolution |
|----------|------------|
| Visual mode | Hybrid (3) |
| Location | `apps/web` (decided; Vercel deploy) |
| Approach | A — Scroll-theater SPA |
| Motion/visual | Approved |
| Content/tech | Approved |
