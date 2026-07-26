# Impact Metrics (Phase 1 — Marketing) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the marketing site’s GetIt / `#download` chapter with an illustrative Impact section, and keep Download CTAs in nav + Setup (and existing Hero/Footer links).

**Architecture:** Static content in `apps/web/src/content.ts` drives a new `Impact` section component. Remove `GetIt`. No new scroll pins (Capabilities + Setup remain the only pins). Phase 2 Desktop/Core telemetry is **out of scope** for this plan — tracked in the design spec only.

**Tech Stack:** Vite 8, React 19, TypeScript, Tailwind CSS v4, Node `node:test` (`apps/web` scripts).

**Spec:** `docs/superpowers/specs/2026-07-26-impact-metrics-design.md`

## Global Constraints

- Touch `apps/web` only in this plan (no Desktop/Core changes)
- Brand: slate `#1c1f22`, teal `#00d1b2`; display Space Grotesk; body DM Sans
- Impact has **no** Download CTA inside the section
- Download Desktop → `https://github.com/Tyler-Hughes312/mycelium/releases`
- Nav: Features · Why · Setup · **Impact** (`#impact`) · **Download** (external Releases)
- Setup footer must add a Download Desktop button; keep install-guide link
- Impact metrics are **illustrative**; disclaimer must include the word `illustrative`
- Pins remain ≤2 (Capabilities + Setup); do not pin Impact
- Skip git commit steps unless the user explicitly asks to commit
- Do not invent cloud analytics or measured site numbers

---

## File map

| File | Responsibility |
|------|----------------|
| `apps/web/src/content.ts` | `IMPACT_INTRO`, `ImpactMetric` type, `IMPACT_METRICS`, `IMPACT_DISCLAIMER` |
| `apps/web/src/content.test.mjs` | Assert Impact ids, token theme, illustrative disclaimer |
| `apps/web/src/components/Impact.tsx` | Impact section UI (`#impact`) |
| `apps/web/src/App.tsx` | Swap `GetIt` → `Impact` |
| `apps/web/src/components/GetIt.tsx` | **Delete** |
| `apps/web/src/components/SiteNav.tsx` | Impact + external Download |
| `apps/web/src/components/Setup.tsx` | Download Desktop button in footer |
| `apps/web/src/components/SiteFooter.tsx` | Add Impact anchor; keep Download → Releases |

**Deferred (Phase 2 plan later):** Core impact store/APIs, Desktop `/impact` page, Settings toggle.

---

### Task 1: Impact content + tests (TDD)

**Files:**
- Modify: `apps/web/src/content.ts`
- Modify: `apps/web/src/content.test.mjs`
- Test: `apps/web/src/content.test.mjs`

**Interfaces:**
- Consumes: existing `LINKS` / Outcomes patterns in `content.ts`
- Produces:
  - `IMPACT_INTRO: { eyebrow, headline, sub }`
  - `type ImpactMetric = { id: string; stat: string; title: string; body: string }`
  - `IMPACT_METRICS: ImpactMetric[]` with ids `tokens` | `packet` | `reuse` | `grounded`
  - `IMPACT_DISCLAIMER: string` containing `illustrative`

- [x] **Step 1: Write the failing test**

Append to `apps/web/src/content.test.mjs`:

```js
test("impact metrics cover tokens packet reuse grounded with illustrative disclaimer", async () => {
  const { IMPACT_INTRO, IMPACT_METRICS, IMPACT_DISCLAIMER } = await import(
    "./content.ts"
  );
  assert.equal(IMPACT_INTRO.eyebrow, "Impact");
  assert.match(IMPACT_INTRO.headline.toLowerCase(), /token|fewer|sharper/);
  assert.deepEqual(
    IMPACT_METRICS.map((m) => m.id),
    ["tokens", "packet", "reuse", "grounded"],
  );
  for (const m of IMPACT_METRICS) {
    assert.ok(m.stat.length > 0, `${m.id} needs a display stat`);
    assert.ok(m.title.length > 0, `${m.id} needs a title`);
    assert.ok(m.body.length > 0, `${m.id} needs a body`);
  }
  const blob = IMPACT_METRICS.map((m) => `${m.stat} ${m.title} ${m.body}`)
    .join(" ")
    .toLowerCase();
  assert.match(blob, /token/);
  assert.match(IMPACT_DISCLAIMER.toLowerCase(), /illustrative/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd apps/web && npm test
```

Expected: FAIL — `IMPACT_INTRO` / `IMPACT_METRICS` / `IMPACT_DISCLAIMER` not exported.

- [ ] **Step 3: Add content constants**

Append to `apps/web/src/content.ts` (after `SETUP_STEPS`):

```ts
export const IMPACT_INTRO = {
  eyebrow: "Impact",
  headline: "Fewer tokens. Sharper code. Same machine.",
  sub: "Mycelium retrieves the slices that matter — so agents spend context on answers, not haystacks, and your conventions travel with every recall.",
} as const;

export type ImpactMetric = {
  id: string;
  stat: string;
  title: string;
  body: string;
};

export const IMPACT_METRICS: ImpactMetric[] = [
  {
    id: "tokens",
    stat: "~60–90%",
    title: "Fewer context tokens",
    body: "Focus and search packets beat dumping whole files — spend the window on the answer, not the haystack.",
  },
  {
    id: "packet",
    stat: "1 packet",
    title: "Per question",
    body: "Symbols, commits, and notes that match the ask — not half the repo pasted into every chat.",
  },
  {
    id: "reuse",
    stat: "Library-wide",
    title: "Reuse without re-paste",
    body: "Find the auth helper, fixture, or ADR you already shipped in another imported repo.",
  },
  {
    id: "grounded",
    stat: "Your patterns",
    title: "Grounded outputs",
    body: "Answers match naming, error handling, and decisions you already use — less generic advice.",
  },
];

export const IMPACT_DISCLAIMER =
  "Illustrative of typical sessions — your Desktop app will track live savings once telemetry ships.";
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
cd apps/web && npm test
```

Expected: PASS (all tests green, including the new Impact test).

- [ ] **Step 5: Commit (only if user asked)**

```bash
git add apps/web/src/content.ts apps/web/src/content.test.mjs
git commit -m "$(cat <<'EOF'
feat(web): add Impact content constants and tests

Lock illustrative metrics and disclaimer copy for the marketing Impact section.
EOF
)"
```

---

### Task 2: Impact section + remove GetIt

**Files:**
- Create: `apps/web/src/components/Impact.tsx`
- Modify: `apps/web/src/App.tsx`
- Delete: `apps/web/src/components/GetIt.tsx`

**Interfaces:**
- Consumes: `IMPACT_INTRO`, `IMPACT_METRICS`, `IMPACT_DISCLAIMER` from `../content`
- Produces: `export function Impact(): JSX.Element` with `id="impact"` and `data-chapter="impact"`

- [ ] **Step 1: Create `Impact.tsx`**

Create `apps/web/src/components/Impact.tsx`:

```tsx
import { IMPACT_DISCLAIMER, IMPACT_INTRO, IMPACT_METRICS } from "../content";

export function Impact() {
  return (
    <section
      id="impact"
      data-chapter="impact"
      className="relative overflow-hidden bg-[var(--color-bg)] px-6 py-28"
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse at 20% 10%, rgba(0, 209, 178, 0.14), transparent 50%), radial-gradient(ellipse at 85% 60%, rgba(123, 108, 246, 0.1), transparent 45%)",
        }}
      />
      <div className="relative z-10 mx-auto max-w-5xl">
        <p className="font-display text-sm font-medium uppercase tracking-[0.2em] text-[var(--color-teal)]">
          {IMPACT_INTRO.eyebrow}
        </p>
        <h2 className="mt-3 max-w-3xl font-display text-4xl font-semibold tracking-tight text-[var(--color-fg)] sm:text-5xl">
          {IMPACT_INTRO.headline}
        </h2>
        <p className="mt-5 max-w-2xl text-lg leading-relaxed text-[var(--color-muted)]">
          {IMPACT_INTRO.sub}
        </p>

        <ul className="mt-14 grid gap-8 sm:grid-cols-2">
          {IMPACT_METRICS.map((metric) => (
            <li key={metric.id} className="border-t border-white/10 pt-6">
              <p className="font-display text-4xl font-semibold tracking-tight text-[var(--color-teal)] sm:text-5xl">
                {metric.stat}
              </p>
              <h3 className="mt-3 font-display text-xl font-semibold tracking-tight text-[var(--color-fg)]">
                {metric.title}
              </h3>
              <p className="mt-2 max-w-md text-base leading-relaxed text-[var(--color-muted)]">
                {metric.body}
              </p>
            </li>
          ))}
        </ul>

        <p className="mt-12 max-w-2xl text-sm leading-relaxed text-[var(--color-muted)]">
          {IMPACT_DISCLAIMER}
        </p>
      </div>
    </section>
  );
}
```

Do **not** add Download buttons in this component.

- [ ] **Step 2: Wire `App.tsx`**

Replace GetIt import/usage with Impact:

```tsx
import { useRef } from "react";
import { useScrollTheater } from "./hooks/useScrollTheater";
import { SiteNav } from "./components/SiteNav";
import { Hero } from "./components/Hero";
import { Outcomes } from "./components/Outcomes";
import { Capabilities } from "./components/Capabilities";
import { Setup } from "./components/Setup";
import { Impact } from "./components/Impact";
import { SiteFooter } from "./components/SiteFooter";

export default function App() {
  const rootRef = useRef<HTMLDivElement>(null);
  useScrollTheater(rootRef);

  return (
    <div ref={rootRef}>
      <SiteNav />
      <main>
        <Hero />
        <Capabilities />
        <Outcomes />
        <Setup />
        <Impact />
      </main>
      <SiteFooter />
    </div>
  );
}
```

Preserve the existing chapter order in `App.tsx` (Capabilities before Outcomes) — only replace GetIt → Impact.

- [ ] **Step 3: Delete `GetIt.tsx`**

```bash
rm apps/web/src/components/GetIt.tsx
```

Confirm no remaining imports:

```bash
rg "GetIt|#download|get-it" apps/web/src
```

Expected: no `GetIt` / `get-it` hits; `#download` may still appear until Task 3 updates nav (allowed).

- [ ] **Step 4: Typecheck / build**

Run:

```bash
cd apps/web && npm run build
```

Expected: PASS (`tsc -b && vite build` succeeds).

- [ ] **Step 5: Commit (only if user asked)**

```bash
git add apps/web/src/components/Impact.tsx apps/web/src/App.tsx
git rm apps/web/src/components/GetIt.tsx
git commit -m "$(cat <<'EOF'
feat(web): replace GetIt chapter with Impact section

Surface illustrative token-savings metrics instead of a dedicated download block.
EOF
)"
```

---

### Task 3: Nav + Setup Download CTAs + footer Impact link

**Files:**
- Modify: `apps/web/src/components/SiteNav.tsx`
- Modify: `apps/web/src/components/Setup.tsx`
- Modify: `apps/web/src/components/SiteFooter.tsx`

**Interfaces:**
- Consumes: `LINKS.releases`, `LINKS.desktopInstallDoc`
- Produces: Nav anchors `#impact` + external Download; Setup footer Download button; Footer `#impact` link

- [ ] **Step 1: Update `SiteNav.tsx`**

Replace `NAV_LINKS` and the Download treatment so Impact is in-page and Download is external:

```tsx
import { LINKS } from "../content";

const NAV_LINKS = [
  { href: "#features", label: "Features" },
  { href: "#why", label: "Why" },
  { href: "#setup", label: "Setup" },
  { href: "#impact", label: "Impact" },
] as const;

const linkClass =
  "cursor-pointer rounded-sm transition-colors duration-200 hover:text-[var(--color-teal)]";

export function SiteNav() {
  return (
    <header className="site-nav fixed inset-x-0 top-0 z-50 border-b border-white/5">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <a href="#" className={`flex items-center gap-3 ${linkClass}`}>
          <img
            src="/logo-E-slate-teal.svg"
            alt="Mycelium"
            className="h-8 w-8 rounded-md"
          />
          <span className="font-display text-lg font-semibold tracking-tight text-[var(--color-fg)]">
            Mycelium
          </span>
        </a>
        <ul className="flex flex-wrap items-center justify-end gap-x-5 gap-y-2 text-sm font-medium text-[var(--color-muted)]">
          {NAV_LINKS.map((link) => (
            <li key={link.href}>
              <a href={link.href} className={linkClass}>
                {link.label}
              </a>
            </li>
          ))}
          <li>
            <a
              href={LINKS.releases}
              target="_blank"
              rel="noreferrer"
              className={linkClass}
            >
              Download
            </a>
          </li>
          <li>
            <a
              href={LINKS.github}
              target="_blank"
              rel="noreferrer"
              className={linkClass}
            >
              GitHub
            </a>
          </li>
        </ul>
      </nav>
    </header>
  );
}
```

- [ ] **Step 2: Update Setup footer with Download button**

In `apps/web/src/components/Setup.tsx`, replace the trailing `<p className="mt-10 ...">` block with:

```tsx
        <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:items-center">
          <a
            href={LINKS.releases}
            target="_blank"
            rel="noreferrer"
            className="btn-primary"
          >
            Download Desktop
          </a>
          <p className="text-sm text-[var(--color-muted)]">
            macOS Gatekeeper / Windows SmartScreen notes:{" "}
            <a
              href={LINKS.desktopInstallDoc}
              target="_blank"
              rel="noreferrer"
              className="cursor-pointer text-[var(--color-teal)] underline-offset-4 transition-colors duration-200 hover:underline"
            >
              Desktop install guide
            </a>
            .
          </p>
        </div>
```

- [ ] **Step 3: Add Impact link in footer**

In `apps/web/src/components/SiteFooter.tsx`, after the Setup `<li>`, insert:

```tsx
            <li>
              <a href="#impact" className={footerLink}>
                Impact
              </a>
            </li>
```

Keep the existing Download footer item pointing at `LINKS.releases`.

- [ ] **Step 4: Verify no stale `#download` anchors**

Run:

```bash
rg "#download|GetIt|get-it" apps/web/src
```

Expected: no matches.

- [ ] **Step 5: Run tests + build**

```bash
cd apps/web && npm test && npm run build
```

Expected: PASS.

- [ ] **Step 6: Manual smoke (dev server)**

```bash
cd apps/web && npm run dev
```

Check:

1. Nav **Impact** scrolls to `#impact`
2. Nav **Download** opens GitHub Releases
3. Setup shows **Download Desktop** + install guide
4. Impact shows four metrics + illustrative disclaimer
5. No dedicated GetIt / download chapter

- [ ] **Step 7: Commit (only if user asked)**

```bash
git add apps/web/src/components/SiteNav.tsx apps/web/src/components/Setup.tsx apps/web/src/components/SiteFooter.tsx
git commit -m "$(cat <<'EOF'
feat(web): move Download CTAs to nav and Setup

Keep Impact metrics-focused while preserving one-click Desktop install.
EOF
)"
```

---

### Task 4: Mark Phase 1 ready in the design spec

**Files:**
- Modify: `docs/superpowers/specs/2026-07-26-impact-metrics-design.md` (status line only)

**Interfaces:**
- Consumes: completed Phase 1 tasks
- Produces: Spec status notes Phase 1 plan path

- [ ] **Step 1: Update status header**

Change the status line near the top of the design spec to:

```markdown
**Status:** Phase 1 plan at `docs/superpowers/plans/2026-07-26-impact-metrics-web.md` — Phase 2 Desktop telemetry still follow-up  
```

- [ ] **Step 2: Commit (only if user asked)**

```bash
git add docs/superpowers/specs/2026-07-26-impact-metrics-design.md docs/superpowers/plans/2026-07-26-impact-metrics-web.md
git commit -m "$(cat <<'EOF'
docs: link Impact Phase 1 plan from design spec
EOF
)"
```

---

## Spec coverage checklist

| Spec requirement | Task |
|------------------|------|
| Replace GetIt / `#download` with Impact | Task 2 |
| `IMPACT_*` content + illustrative disclaimer | Task 1 |
| Four metrics (tokens, packet, reuse, grounded) | Task 1–2 |
| No Download CTA inside Impact | Task 2 |
| Nav Impact + external Download | Task 3 |
| Setup footer Download button | Task 3 |
| Footer keeps Download; add Impact | Task 3 |
| No new scroll pin | Task 2 (no theater changes) |
| Phase 2 Core/Desktop | Deferred — separate plan |

## Self-review notes

- No TBD/placeholder steps; full copy and component code inlined.
- Names consistent: `IMPACT_INTRO`, `IMPACT_METRICS`, `IMPACT_DISCLAIMER`, `Impact` component, `#impact`.
- Phase 2 explicitly deferred so this plan stays shippable alone.
