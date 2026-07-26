# Mycelium Marketing Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a scroll-theater marketing site in `apps/web` that sells Mycelium (capabilities, setup, Desktop download + GitHub) with Lenis + GSAP motion for Vercel.

**Architecture:** Vite + React + TypeScript SPA. One long page with chapter components. Shared motion boot (`useScrollTheater`) owns Lenis + ScrollTrigger lifecycle and reduced-motion branching. Stitch comps + logo SVG land in `public/`. Tokens live in CSS variables aligned to the hybrid slate/teal + chapter poster washes.

**Tech Stack:** Vite 8, React 19, TypeScript, Tailwind CSS v4, GSAP + ScrollTrigger, Lenis, Node `node:test` for link/constant tests.

**Spec:** `docs/superpowers/specs/2026-07-26-mycelium-marketing-site-design.md`

## Global Constraints

- App path: `apps/web` only (do not put marketing UI in `apps/desktop`)
- Brand product surfaces: slate `#1c1f22`, teal `#00d1b2` (Logo E / marketing product world)
- Chapter explosions: vivid poster washes (magenta / sage / violet) — teal remains signature accent
- Display font: Space Grotesk; body: DM Sans
- CTAs: Desktop → `https://github.com/Tyler-Hughes312/mycelium/releases`; GitHub → `https://github.com/Tyler-Hughes312/mycelium`
- Pins: Capabilities + Setup only (≤2); respect `prefers-reduced-motion`
- No transparent-video pipeline in v1; no emoji icons; no purple SaaS gradient defaults
- Vercel: root `apps/web`, build `npm run build`, output `dist`, no env secrets
- Skip git commit steps if the user has not asked to commit; never `git init`

---

## File map

| File | Responsibility |
|------|----------------|
| `apps/web/package.json` | Web app deps + scripts |
| `apps/web/vite.config.ts` | Vite + React + Tailwind plugin |
| `apps/web/tsconfig.json` / `tsconfig.app.json` | TS project |
| `apps/web/index.html` | Shell + font preconnect |
| `apps/web/vercel.json` | Static SPA headers (optional rewrite) |
| `apps/web/README.md` | Dev + Vercel deploy notes |
| `apps/web/design-system/MASTER.md` | Persisted ui-ux-pro-max system |
| `apps/web/src/main.tsx` | React mount |
| `apps/web/src/App.tsx` | Page composition + nav anchors |
| `apps/web/src/index.css` | Tokens, fonts, base layout |
| `apps/web/src/content.ts` | Locked copy + URLs (single source) |
| `apps/web/src/content.test.mjs` | Assert CTA URLs + capability titles |
| `apps/web/src/hooks/useScrollTheater.ts` | Lenis + GSAP + reduced motion |
| `apps/web/src/hooks/prefersReducedMotion.ts` | Media-query helper |
| `apps/web/src/hooks/prefersReducedMotion.test.mjs` | Unit test for helper |
| `apps/web/src/components/SiteNav.tsx` | Fixed nav |
| `apps/web/src/components/Hero.tsx` | Hero chapter |
| `apps/web/src/components/Capabilities.tsx` | Pinned horizontal journey |
| `apps/web/src/components/Setup.tsx` | Pinned setup steps |
| `apps/web/src/components/GetIt.tsx` | Download + GitHub |
| `apps/web/src/components/SiteFooter.tsx` | Footer |
| `apps/web/src/components/HyphaStroke.tsx` | SVG hypha draw accent |
| `apps/web/public/logo-E-slate-teal.svg` | Brand mark |
| `apps/web/public/stitch/` | Stitch exports / placeholders |

---

### Task 1: Design system persist + Stitch art direction

**Files:**
- Create: `apps/web/design-system/MASTER.md` (via ui-ux-pro-max `--persist`)
- Create: Stitch screens in existing Stitch project `1582993350217593804` (Mycelium)
- Create: `apps/web/public/stitch/.gitkeep` (assets filled when exports available)

**Interfaces:**
- Consumes: ui-ux-pro-max CLI scripts at `.cursor/skills/ui-ux-pro-max/scripts/search.py`; Stitch MCP `generate_screen_from_text`
- Produces: `MASTER.md` tokens for Task 2 CSS; Stitch comps referenced by capability card `image` paths under `/stitch/`

- [ ] **Step 1: Persist design system**

Run from repo root:

```bash
mkdir -p apps/web
python3 .cursor/skills/ui-ux-pro-max/scripts/search.py \
  "developer tool local-first AI context layer marketing scroll storytelling mycelium" \
  --design-system --persist --motion 9 --variance 7 \
  -p "Mycelium" \
  --page "marketing"
# Move/copy generated design-system/ into apps/web/design-system/ if CLI wrote at CWD
```

If the CLI writes `./design-system/` at CWD, move it:

```bash
mv design-system apps/web/design-system 2>/dev/null || true
ls apps/web/design-system/MASTER.md
```

Expected: `MASTER.md` exists with colors, typography, motion notes.

- [ ] **Step 2: Override MASTER brand hexes to Mycelium product world**

Edit `apps/web/design-system/MASTER.md` so product anchors match the spec (not the green SaaS default from the skill):

- Primary / accent: `#00d1b2`
- Background: `#1c1f22`
- Foreground: `#f2f4f5`
- Note chapter washes: magenta `#E83A7A`, sage `#7CB69A`, violet `#7B6CF6` for Capabilities/Setup only

- [ ] **Step 3: Generate Stitch desktop screens (do not retry on timeout)**

Using Stitch MCP `generate_screen_from_text` with `projectId: "1582993350217593804"`, `deviceType: "DESKTOP"`, `modelId: "GEMINI_3_FLASH"`:

1. Prompt: `Mycelium marketing hero — dark slate #1c1f22 background, teal #00d1b2 accents, large Space Grotesk headline "Local-first context layer", logo mark top-left, dual CTAs Download and GitHub, subtle hypha line art, no purple gradients`
2. Prompt: `Mycelium capabilities horizontal strip — five vivid poster cards Library Index Search Vault Agents, hybrid dark chrome with magenta sage violet washes, product UI mock insets, teal accents`
3. Prompt: `Mycelium setup chapter — three numbered steps clone install.sh, dev.sh, Library Index Search, high contrast dark UI, teal highlights`
4. Prompt: `Mycelium download chapter — Download Desktop and GitHub CTAs, slate teal product world, calm after vivid chapters`

If a call times out, poll `get_screen` / `list_screens` — do not re-fire generation.

- [ ] **Step 4: Export placeholders**

```bash
mkdir -p apps/web/public/stitch
touch apps/web/public/stitch/.gitkeep
```

When Stitch HTML/screenshots are available, save under `apps/web/public/stitch/` as `hero.png`, `capabilities.png`, `setup.png`, `download.png` (or SVG). Until then, components use CSS poster panels.

- [ ] **Step 5: Commit (only if user requested)**

```bash
git add apps/web/design-system apps/web/public/stitch
git commit -m "$(cat <<'EOF'
docs: persist Mycelium marketing design system and stitch assets folder

EOF
)"
```

---

### Task 2: Scaffold `apps/web` + content constants with tests

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/vite.config.ts`
- Create: `apps/web/tsconfig.json`, `apps/web/tsconfig.app.json`, `apps/web/tsconfig.node.json`
- Create: `apps/web/index.html`
- Create: `apps/web/src/main.tsx`
- Create: `apps/web/src/App.tsx` (stub)
- Create: `apps/web/src/index.css` (tokens)
- Create: `apps/web/src/content.ts`
- Create: `apps/web/src/content.test.mjs`
- Create: `apps/web/vercel.json`
- Create: `apps/web/README.md`
- Create: `apps/web/public/logo-E-slate-teal.svg` (copy from `apps/logo-E-slate-teal.svg`)

**Interfaces:**
- Consumes: design tokens from Task 1 / spec hexes
- Produces: `export const LINKS`, `export const HERO`, `export const CAPABILITIES`, `export const SETUP_STEPS` from `content.ts`

- [ ] **Step 1: Write failing content test**

Create `apps/web/src/content.test.mjs`:

```js
import assert from "node:assert/strict";
import { test } from "node:test";

test("CTA URLs point at official Mycelium repo", async () => {
  const { LINKS } = await import("./content.ts");
  assert.equal(LINKS.releases, "https://github.com/Tyler-Hughes312/mycelium/releases");
  assert.equal(LINKS.github, "https://github.com/Tyler-Hughes312/mycelium");
  assert.equal(LINKS.desktopInstallDoc, "https://github.com/Tyler-Hughes312/mycelium/blob/main/docs/DESKTOP-INSTALL.md");
});

test("capabilities cover five surfaces in order", async () => {
  const { CAPABILITIES } = await import("./content.ts");
  assert.deepEqual(
    CAPABILITIES.map((c) => c.id),
    ["library", "index", "search", "vault", "agents"],
  );
});
```

- [ ] **Step 2: Run test — expect FAIL (module missing)**

```bash
cd apps/web && node --experimental-strip-types --test src/content.test.mjs
```

Expected: FAIL resolving `./content.ts`

- [ ] **Step 3: Create package + Vite scaffold**

`apps/web/package.json`:

```json
{
  "name": "mycelium-web",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "test": "node --experimental-strip-types --test src/**/*.test.mjs"
  },
  "dependencies": {
    "gsap": "^3.13.0",
    "lenis": "^1.3.4",
    "react": "^19.2.7",
    "react-dom": "^19.2.7"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.3.3",
    "@types/react": "^19.2.17",
    "@types/react-dom": "^19.2.3",
    "@vitejs/plugin-react": "^6.0.3",
    "tailwindcss": "^4.3.3",
    "typescript": "~6.0.2",
    "vite": "^8.1.1"
  }
}
```

`apps/web/vite.config.ts`:

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
});
```

Mirror `apps/desktop` tsconfig patterns (`strict`, `jsx: react-jsx`, `moduleResolution: bundler`). `index.html` root `#root` → `/src/main.tsx`.

- [ ] **Step 4: Implement `content.ts` + CSS tokens + stub App**

`apps/web/src/content.ts`:

```ts
export const LINKS = {
  releases: "https://github.com/Tyler-Hughes312/mycelium/releases",
  github: "https://github.com/Tyler-Hughes312/mycelium",
  desktopInstallDoc:
    "https://github.com/Tyler-Hughes312/mycelium/blob/main/docs/DESKTOP-INSTALL.md",
} as const;

export const HERO = {
  brand: "Mycelium",
  headline: "Local-first context layer for AI-heavy developers",
  sub: "Code + Thinking Vault stay on 127.0.0.1. No cloud account required.",
} as const;

export type Capability = {
  id: "library" | "index" | "search" | "vault" | "agents";
  title: string;
  body: string;
  wash: "magenta" | "sage" | "violet" | "teal" | "slate";
};

export const CAPABILITIES: Capability[] = [
  {
    id: "library",
    title: "Library",
    body: "Import repos so Search can reuse old code across projects.",
    wash: "magenta",
  },
  {
    id: "index",
    title: "Index",
    body: "Local embeddings and indexes under ~/.mycelium.",
    wash: "sage",
  },
  {
    id: "search",
    title: "Search",
    body: "Hybrid recall over symbols, commits, files, and vault notes.",
    wash: "violet",
  },
  {
    id: "vault",
    title: "Vault",
    body: "Markdown second brain with buckets and wikilinks.",
    wash: "teal",
  },
  {
    id: "agents",
    title: "Agents",
    body: "MCP tools for Cursor / Claude against Core on :8787.",
    wash: "slate",
  },
];

export const SETUP_STEPS = [
  {
    n: 1,
    title: "Install",
    body: "Clone the repo and run ./scripts/install.sh",
  },
  {
    n: 2,
    title: "Run",
    body: "./scripts/dev.sh — Core :8787 + Desktop — or open packaged Desktop from Releases",
  },
  {
    n: 3,
    title: "Use",
    body: "Library → Index → Search. Try the dogfood fixture from the README.",
  },
] as const;
```

`apps/web/src/index.css` (excerpt — full file must define all vars):

```css
@import url("https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Grotesk:wght@400;500;600;700&display=swap");
@import "tailwindcss";

:root {
  --color-bg: #1c1f22;
  --color-fg: #f2f4f5;
  --color-muted: #9aa3aa;
  --color-teal: #00d1b2;
  --color-surface: #262a2e;
  --color-wash-magenta: #e83a7a;
  --color-wash-sage: #7cb69a;
  --color-wash-violet: #7b6cf6;
  --font-display: "Space Grotesk", sans-serif;
  --font-body: "DM Sans", sans-serif;
}

html,
body,
#root {
  min-height: 100%;
  background: var(--color-bg);
  color: var(--color-fg);
  font-family: var(--font-body);
}

h1,
h2,
h3 {
  font-family: var(--font-display);
}
```

Copy logo:

```bash
cp apps/logo-E-slate-teal.svg apps/web/public/logo-E-slate-teal.svg
```

`apps/web/vercel.json`:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite"
}
```

`apps/web/README.md`: document `npm install && npm run dev`, Vercel root `apps/web`.

Stub `App.tsx` returning `<main><h1>Mycelium</h1></main>`.

- [ ] **Step 5: Install + run tests + build smoke**

```bash
cd apps/web && npm install && npm test && npm run build
```

Expected: tests PASS; `dist/` produced.

- [ ] **Step 6: Commit (only if user requested)**

```bash
git add apps/web
git commit -m "$(cat <<'EOF'
feat(web): scaffold marketing app with locked content constants

EOF
)"
```

---

### Task 3: Reduced-motion helper + scroll theater hook

**Files:**
- Create: `apps/web/src/hooks/prefersReducedMotion.ts`
- Create: `apps/web/src/hooks/prefersReducedMotion.test.mjs`
- Create: `apps/web/src/hooks/useScrollTheater.ts`

**Interfaces:**
- Consumes: `gsap`, `ScrollTrigger`, `lenis`
- Produces:
  - `export function getPrefersReducedMotion(): boolean`
  - `export function useScrollTheater(rootRef: RefObject<HTMLElement | null>): void` — initializes Lenis + registers GSAP contexts; cleans up on unmount

- [ ] **Step 1: Write failing reduced-motion test**

```js
import assert from "node:assert/strict";
import { test } from "node:test";

test("getPrefersReducedMotion reads matchMedia when available", async () => {
  const { getPrefersReducedMotion } = await import("./prefersReducedMotion.ts");
  globalThis.matchMedia = (query) => ({
    matches: query.includes("prefers-reduced-motion"),
    media: query,
    addEventListener() {},
    removeEventListener() {},
    dispatchEvent() {
      return false;
    },
    onchange: null,
    addListener() {},
    removeListener() {},
  });
  assert.equal(getPrefersReducedMotion(), true);
});
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd apps/web && node --experimental-strip-types --test src/hooks/prefersReducedMotion.test.mjs
```

- [ ] **Step 3: Implement helper + hook**

`prefersReducedMotion.ts`:

```ts
export function getPrefersReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}
```

`useScrollTheater.ts` sketch (full implementation must kill tweens on cleanup):

```ts
import { useEffect, type RefObject } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import { getPrefersReducedMotion } from "./prefersReducedMotion";

gsap.registerPlugin(ScrollTrigger);

export function useScrollTheater(rootRef: RefObject<HTMLElement | null>): void {
  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;

    const reduced = getPrefersReducedMotion();
    if (reduced) {
      root.dataset.motion = "reduced";
      return;
    }

    root.dataset.motion = "full";
    const lenis = new Lenis({ autoRaf: true });
    lenis.on("scroll", ScrollTrigger.update);

    const ctx = gsap.context(() => {
      // Capabilities horizontal scrub
      const caps = root.querySelector<HTMLElement>("[data-chapter='capabilities']");
      const track = root.querySelector<HTMLElement>("[data-caps-track]");
      if (caps && track) {
        const total = track.scrollWidth - caps.clientWidth;
        gsap.to(track, {
          x: () => -Math.max(total, 0),
          ease: "none",
          scrollTrigger: {
            trigger: caps,
            start: "top top",
            end: () => `+=${Math.max(total, caps.clientHeight)}`,
            pin: true,
            scrub: 1,
            invalidateOnRefresh: true,
          },
        });
      }

      // Setup pin + step reveals
      const setup = root.querySelector<HTMLElement>("[data-chapter='setup']");
      if (setup) {
        const steps = setup.querySelectorAll("[data-setup-step]");
        gsap
          .timeline({
            scrollTrigger: {
              trigger: setup,
              start: "top top",
              end: "+=120%",
              pin: true,
              scrub: 1,
            },
          })
          .from(steps, { opacity: 0.15, y: 40, stagger: 0.2 });
      }

      // Hero hypha + type
      gsap.from(root.querySelectorAll("[data-hero-animate]"), {
        opacity: 0,
        y: 32,
        duration: 1,
        stagger: 0.12,
        ease: "power2.out",
      });
    }, root);

    const onLoad = () => ScrollTrigger.refresh();
    window.addEventListener("load", onLoad);

    return () => {
      window.removeEventListener("load", onLoad);
      ctx.revert();
      lenis.destroy();
      ScrollTrigger.getAll().forEach((t) => t.kill());
    };
  }, [rootRef]);
}
```

- [ ] **Step 4: Run tests**

```bash
cd apps/web && npm test
```

Expected: PASS (including content + reduced-motion).

- [ ] **Step 5: Commit (only if user requested)**

---

### Task 4: Static chapters (Hero, Capabilities, Setup, Get it, Footer, Nav)

**Files:**
- Create: `apps/web/src/components/SiteNav.tsx`
- Create: `apps/web/src/components/Hero.tsx`
- Create: `apps/web/src/components/Capabilities.tsx`
- Create: `apps/web/src/components/Setup.tsx`
- Create: `apps/web/src/components/GetIt.tsx`
- Create: `apps/web/src/components/SiteFooter.tsx`
- Create: `apps/web/src/components/HyphaStroke.tsx`
- Modify: `apps/web/src/App.tsx`

**Interfaces:**
- Consumes: `HERO`, `CAPABILITIES`, `SETUP_STEPS`, `LINKS` from `content.ts`; `useScrollTheater`
- Produces: DOM with `data-chapter`, `data-caps-track`, `data-setup-step`, `data-hero-animate`, section ids `#features` `#setup` `#download` for nav

- [ ] **Step 1: Implement SiteNav**

Fixed top nav: logo (`/logo-E-slate-teal.svg` + wordmark Mycelium), anchor links `#features` `#setup` `#download`, external GitHub. Use `cursor-pointer`, teal hover 150–300ms, visible focus rings.

- [ ] **Step 2: Implement Hero**

Full-viewport section, brand-first (logo + **Mycelium** must dominate first viewport), one headline, one sub, dual CTAs (`LINKS.releases`, `LINKS.github`), `HyphaStroke` background SVG with `stroke-dashoffset` ready for GSAP, `data-hero-animate` on text blocks. No cards in hero. No emoji.

- [ ] **Step 3: Implement Capabilities**

`id="features"` `data-chapter="capabilities"` pinned container; inner `data-caps-track` flex row of five full-viewport-ish cards; each card uses `wash` CSS var / class for poster color; title + body from `CAPABILITIES`. Optional `<img src="/stitch/capabilities.png">` if present.

- [ ] **Step 4: Implement Setup**

`id="setup"` `data-chapter="setup"`; three `data-setup-step` blocks from `SETUP_STEPS`; link to `LINKS.desktopInstallDoc` for Gatekeeper notes.

- [ ] **Step 5: Implement GetIt + Footer**

`id="download"`: primary button Download Desktop → `LINKS.releases`; secondary View on GitHub → `LINKS.github`; note packaged Core. Footer: MIT, local-first blurb, same links.

- [ ] **Step 6: Wire App**

```tsx
import { useRef } from "react";
import { useScrollTheater } from "./hooks/useScrollTheater";
import { SiteNav } from "./components/SiteNav";
import { Hero } from "./components/Hero";
import { Capabilities } from "./components/Capabilities";
import { Setup } from "./components/Setup";
import { GetIt } from "./components/GetIt";
import { SiteFooter } from "./components/SiteFooter";

export default function App() {
  const rootRef = useRef<HTMLElement>(null);
  useScrollTheater(rootRef);
  return (
    <div ref={rootRef as React.RefObject<HTMLDivElement>}>
      <SiteNav />
      <main>
        <Hero />
        <Capabilities />
        <Setup />
        <GetIt />
      </main>
      <SiteFooter />
    </div>
  );
}
```

- [ ] **Step 7: Visual verify**

```bash
cd apps/web && npm run dev
```

Check: first viewport brand-first; CTAs correct; five capability cards; three setup steps; mobile stacks without horizontal overflow when reduced / narrow (CSS `overflow-x: hidden` on body).

- [ ] **Step 8: Commit (only if user requested)**

---

### Task 5: Motion polish + mobile degrade + Vercel readiness

**Files:**
- Modify: `apps/web/src/hooks/useScrollTheater.ts`
- Modify: `apps/web/src/index.css`
- Modify: `apps/web/src/components/*` as needed for `data-motion` CSS
- Modify: `apps/web/README.md`
- Modify: root `README.md` (one-line link to marketing app — optional)

**Interfaces:**
- Consumes: `data-motion="reduced"|"full"` on root
- Produces: desktop scrub theater; mobile (`max-width: 768px`) skips pin or uses shorter end distances; reduced-motion CSS fades only

- [ ] **Step 1: Mobile / reduced CSS**

```css
[data-motion="reduced"] [data-caps-track] {
  transform: none !important;
  flex-wrap: wrap;
}
@media (max-width: 768px) {
  [data-caps-track] {
    flex-direction: column;
  }
}
```

In `useScrollTheater`, if `window.matchMedia("(max-width: 768px)").matches`, skip pin timelines (same as reduced) OR use non-pin scrub only — prefer skip pins on mobile per spec.

- [ ] **Step 2: Hero hypha draw**

Animate `HyphaStroke` path `strokeDashoffset` 1→0 on load when `data-motion="full"`.

- [ ] **Step 3: Build + preview**

```bash
cd apps/web && npm test && npm run build && npm run preview
```

Expected: PASS; preview at `:4173` (or Vite default).

- [ ] **Step 4: Manual acceptance checklist**

- [ ] Hero reads Mycelium (logo + slate/teal)
- [ ] Capabilities communicates five surfaces
- [ ] Setup shows three steps
- [ ] Download + GitHub URLs correct
- [ ] Desktop scroll theater works; mobile degrades
- [ ] `prefers-reduced-motion: reduce` disables pins (DevTools emulation)
- [ ] `apps/web/README.md` documents Vercel root/build/output

- [ ] **Step 5: Commit (only if user requested)**

```bash
git add apps/web
git commit -m "$(cat <<'EOF'
feat(web): ship Mycelium scroll-theater marketing site

EOF
)"
```

---

## Spec coverage (self-review)

| Spec requirement | Task |
|------------------|------|
| Capabilities / setup / download / GitHub | 2, 4 |
| Scroll theater Lenis + GSAP | 3, 5 |
| Hybrid visual + fonts | 1, 2, 4 |
| ≤2 pins + reduced motion | 3, 5 |
| `apps/web` + Vercel | 2, 5 |
| Stitch + ui-ux-pro-max | 1 |
| No transparent video v1 | Out of scope (hypha SVG instead) |
| Acceptance criteria | Task 5 checklist |

## Placeholder scan

No TBD / “implement later” left in tasks. Commit steps gated on user request.
