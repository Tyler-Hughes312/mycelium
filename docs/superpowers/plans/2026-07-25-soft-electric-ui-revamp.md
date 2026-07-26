# Soft Electric UI Revamp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernize Mycelium desktop UI with a soft-electric light-blue accent (no glow), replacing hypha green across tokens, shell, and all primary pages.

**Architecture:** Keep token *names* (`primary`, `accent-hypha`, etc.) and change *values* to Soft Electric blues so Tailwind classes keep working. Restyle AppShell and pages for density/radius/selection; selection/focus uses blue, not gold. Sync shared `@mycelium/ui` theme + VS Code panel CSS hex for consistency.

**Tech Stack:** React 19, Tailwind CSS v4 (`@theme` in `apps/desktop/src/index.css`), `@mycelium/ui` shared package, Vite, Node built-in test runner (`node:test`).

**Spec:** `docs/superpowers/specs/2026-07-25-soft-electric-ui-revamp-design.md`

## Global Constraints

- Primary accent hex: `#6EC8FF` (soft electric blue) — fully replaces hypha green for actions, healthy/connected, active nav, wikilinks
- Accent muted / primary-container: `#3A7FA8`
- Accent dim (selection wash): `#1A3A4D`
- Secondary/warn (indexing only): `#E5C276` — never for selection/focus
- Soft electric: clean edges, **almost no glow** (remove gold selection shadows)
- Radius: inputs/rows `8px` (`rounded-lg` or explicit); primary buttons `10px`
- Motion: ~150ms color/border only; indexing status dot pulse OK
- Keep IBM Plex Sans + Mono; mono only for paths/SHAs/logs
- Do not redesign IA or add screens; do not rewrite Stitch HTML mockups
- Workspace may have **no git repo** — skip commit steps if `git status` fails; never `git init` unless the user asks

---

## File map

| File | Responsibility |
|---|---|
| `packages/ui/src/theme.css` | Shared CSS variables (source of Soft Electric values) |
| `packages/ui/src/theme.test.mjs` | Asserts Soft Electric hex values in `theme.css` |
| `apps/desktop/src/index.css` | Tailwind `@theme` colors, radius, `.note-link` |
| `apps/desktop/src/components/AppShell.tsx` | Rail width, CTA, active nav, header cleanup |
| `apps/desktop/src/pages/SearchPage.tsx` | Focus/selection → blue; remove spore glow |
| `apps/desktop/src/pages/LibraryPage.tsx` | Radius/density polish |
| `apps/desktop/src/pages/VaultPage.tsx` | Hardcoded green SVG + accent classes |
| `apps/desktop/src/pages/IndexPage.tsx` | Radius consistency (tokens already drive blue) |
| `apps/desktop/src/pages/SettingsPage.tsx` | Radius + focus border → primary |
| `apps/vscode/media/panel.css` | Match `--primary` to `#6EC8FF` |
| `_bmad-output/.../DESIGN.md` | Document Soft Electric as current design truth |

---

### Task 1: Shared Soft Electric theme tokens

**Files:**
- Modify: `packages/ui/src/theme.css`
- Create: `packages/ui/src/theme.test.mjs`
- Test: `packages/ui/src/theme.test.mjs`

**Interfaces:**
- Consumes: none
- Produces: CSS vars on `:root` — `--mycelium-primary: #6ec8ff`, `--mycelium-accent-hypha: #6ec8ff`, `--mycelium-accent-muted: #3a7fa8`, `--mycelium-accent-dim: #1a3a4d`, `--mycelium-secondary: #e5c276`, `--mycelium-danger: #c45c5c` (names kept; values Soft Electric)

- [ ] **Step 1: Write the failing token test**

Create `packages/ui/src/theme.test.mjs`:

```js
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const root = dirname(fileURLToPath(import.meta.url));
const css = readFileSync(join(root, "theme.css"), "utf8");

function varValue(name) {
  const re = new RegExp(`${name}:\\s*([^;]+);`);
  const m = css.match(re);
  assert.ok(m, `missing ${name}`);
  return m[1].trim().toLowerCase();
}

test("Soft Electric primary replaces hypha green", () => {
  assert.equal(varValue("--mycelium-primary"), "#6ec8ff");
  assert.equal(varValue("--mycelium-accent-hypha"), "#6ec8ff");
  assert.notEqual(varValue("--mycelium-primary"), "#9cd2ba");
});

test("muted/dim accents and warn secondary exist", () => {
  assert.equal(varValue("--mycelium-accent-muted"), "#3a7fa8");
  assert.equal(varValue("--mycelium-accent-dim"), "#1a3a4d");
  assert.equal(varValue("--mycelium-secondary"), "#e5c276");
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/tylerhughes/PlayingAround/MemoryOptimization/packages/ui && node --test src/theme.test.mjs
```

Expected: FAIL — primary still `#9cd2ba` and/or missing `--mycelium-accent-muted` / `--mycelium-accent-dim`.

- [ ] **Step 3: Update `theme.css`**

Replace `packages/ui/src/theme.css` contents with:

```css
/* Mycelium Soft Electric theme tokens (shared) */
:root {
  --mycelium-surface: #111417;
  --mycelium-surface-raised: #161b20;
  --mycelium-surface-overlay: #1c2329;
  --mycelium-background: #111417;
  --mycelium-foreground: #e7ecef;
  --mycelium-muted: #8b979f;
  --mycelium-border: #2a333b;
  --mycelium-primary: #6ec8ff;
  --mycelium-secondary: #e5c276;
  --mycelium-accent-hypha: #6ec8ff;
  --mycelium-accent-spore: #e5c276;
  --mycelium-accent-muted: #3a7fa8;
  --mycelium-accent-dim: #1a3a4d;
  --mycelium-danger: #c45c5c;
  --mycelium-spacing-xs: 4px;
  --mycelium-spacing-sm: 8px;
  --mycelium-spacing-md: 12px;
  --mycelium-spacing-lg: 16px;
  --mycelium-spacing-xl: 24px;
  --mycelium-font-sans: "IBM Plex Sans", sans-serif;
  --mycelium-font-mono: "IBM Plex Mono", monospace;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /Users/tylerhughes/PlayingAround/MemoryOptimization/packages/ui && node --test src/theme.test.mjs
```

Expected: PASS (2 tests).

- [ ] **Step 5: Commit (if git exists)**

```bash
cd /Users/tylerhughes/PlayingAround/MemoryOptimization
git rev-parse --is-inside-work-tree 2>/dev/null || echo "SKIP commit: not a git repo"
# If git exists:
git add packages/ui/src/theme.css packages/ui/src/theme.test.mjs
git commit -m "$(cat <<'EOF'
feat(ui): Soft Electric shared theme tokens

Replace hypha green with #6EC8FF and add muted/dim accents.
EOF
)"
```

---

### Task 2: Desktop Tailwind `@theme` + base styles

**Files:**
- Modify: `apps/desktop/src/index.css`
- Test: verify via build + grep (no separate unit test file)

**Interfaces:**
- Consumes: Soft Electric hex values from Task 1 (same literals mirrored into `@theme`)
- Produces: Tailwind colors `primary`, `accent-hypha`, `accent-dim`, `primary-container`, radius `DEFAULT`/`md`/`lg` aligned to 8px; `.note-link` uses `#6ec8ff`

- [ ] **Step 1: Patch color tokens in `@theme`**

In `apps/desktop/src/index.css`, update these `@theme` entries (keep unrelated Material-ish keys unless they are clearly green primary derivatives):

```css
  --color-inverse-primary: #3a7fa8;
  --color-primary: #6ec8ff;
  --color-on-primary: #001018;
  --color-surface-tint: #6ec8ff;
  --color-primary-fixed-dim: #6ec8ff;
  --color-on-primary-fixed-variant: #1a3a4d;
  --color-primary-fixed: #a8deff;
  --color-primary-container: #3a7fa8;
  --color-on-primary-container: #e7ecef;
  --color-on-primary-fixed: #001018;
  --color-accent-hypha: #6ec8ff;
  --color-accent-spore: #e5c276;
  --color-accent-dim: #1a3a4d;
  --color-accent-muted: #3a7fa8;
```

Also update radius block:

```css
  --radius-DEFAULT: 0.5rem; /* 8px */
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.625rem; /* 10px primary buttons */
  --radius-full: 9999px;
```

- [ ] **Step 2: Update `.note-link` hardcoded greens**

In the same file `@layer base`, change:

```css
  .note-link {
    color: #6ec8ff;
    text-decoration: underline;
    text-decoration-color: #2a333b;
    text-underline-offset: 2px;
    cursor: pointer;
  }

  .note-link:hover {
    text-decoration-color: #6ec8ff;
  }
```

- [ ] **Step 3: Verify no green primary left in desktop theme CSS**

Run:

```bash
cd /Users/tylerhughes/PlayingAround/MemoryOptimization
rg -n "9cd2ba|b7eed6|679b86|003123|002116|346855" apps/desktop/src/index.css packages/ui/src/theme.css || echo "CLEAN"
```

Expected: `CLEAN` (no matches).

- [ ] **Step 4: Typecheck/build desktop**

Run:

```bash
cd /Users/tylerhughes/PlayingAround/MemoryOptimization/apps/desktop && npm run build
```

Expected: `tsc` + `vite build` succeed (exit 0).

- [ ] **Step 5: Commit (if git exists)**

```bash
git add apps/desktop/src/index.css
git commit -m "$(cat <<'EOF'
feat(desktop): Soft Electric Tailwind theme and note-link colors
EOF
)"
```

---

### Task 3: AppShell modernization

**Files:**
- Modify: `apps/desktop/src/components/AppShell.tsx`
- Test: visual via `npm run dev`; structural via build

**Interfaces:**
- Consumes: Tailwind `primary`, `primary-container`, `accent-dim` (via `bg-accent-dim` or arbitrary if needed)
- Produces: Rail `w-[176px]`; CTA label `New note`; active nav uses blue bar + dim tint; header without non-functional avatar; main offset `ml-[176px]` / `w-[calc(100%-176px)]`

- [ ] **Step 1: Update `navClass` active/inactive styles**

Replace `navClass` in `AppShell.tsx` with:

```tsx
function navClass({ isActive }: { isActive: boolean }) {
  return isActive
    ? "flex items-center gap-md py-sm cursor-pointer text-primary border-l-2 border-primary pl-3 bg-accent-dim/80 font-body-sm text-body-sm font-medium transition-colors duration-150"
    : "flex items-center gap-md py-sm cursor-pointer text-muted pl-4 hover:bg-surface-container-high hover:text-on-surface transition-colors duration-150 font-body-sm text-body-sm";
}
```

(Remove `active:scale-95` and `font-bold` — softer modern feel.)

- [ ] **Step 2: Narrow rail + restyle CTA + brand**

In the shell JSX:

1. Change nav `w-[200px]` → `w-[176px]`
2. Change header `w-[calc(100%-200px)]` → `w-[calc(100%-176px)]`
3. Change content wrapper `ml-[200px]` → `ml-[176px]`
4. CTA button classes + label:

```tsx
<button
  type="button"
  className="w-full flex items-center justify-center gap-sm bg-primary text-on-primary hover:brightness-110 py-sm rounded-xl transition-colors duration-150 font-body-sm text-body-sm font-medium"
>
  <span className="material-symbols-outlined text-[16px]">add</span>
  New note
</button>
```

5. Brand icon: keep `account_tree`; ensure `text-primary` (inherits new blue).

- [ ] **Step 3: Clean header**

Remove the non-functional person avatar block at the end of the header trailing actions. Keep `StatusPill` and “Local Only”. Keep hub/terminal buttons only if you leave stubs; preferred: remove both icon buttons for this pass (they are decorative).

Header trailing section should look like:

```tsx
<div className="flex items-center gap-lg">
  <StatusPill connected={coreConnected} label={coreLabel} />
</div>
```

- [ ] **Step 4: Build**

Run:

```bash
cd /Users/tylerhughes/PlayingAround/MemoryOptimization/apps/desktop && npm run build
```

Expected: exit 0.

- [ ] **Step 5: Commit (if git exists)**

```bash
git add apps/desktop/src/components/AppShell.tsx
git commit -m "$(cat <<'EOF'
feat(desktop): modernize AppShell for Soft Electric
EOF
)"
```

---

### Task 4: Search — blue selection, no spore glow

**Files:**
- Modify: `apps/desktop/src/pages/SearchPage.tsx`

**Interfaces:**
- Consumes: `border-primary`, `bg-accent-dim`, `text-primary`
- Produces: Selected result row uses blue border/bar/icon; focus ring on query uses `focus:border-primary`; no `shadow-[0_0_15px_...]`

- [ ] **Step 1: Update query input focus**

Change the search input `className` so `focus:border-accent-spore` becomes `focus:border-primary`, and `rounded-lg` stays (8px). Remove `shadow-sm` if present (borders over shadows):

```tsx
className="w-full bg-surface-container border border-border focus:border-primary outline-none rounded-lg py-4 pl-12 pr-12 font-headline-md text-headline-md text-on-surface transition-colors duration-150"
```

- [ ] **Step 2: Update selected / unselected result row classes**

Replace the selected branch:

```tsx
className={
  isSelected
    ? "group relative flex flex-col gap-1 p-4 rounded-lg bg-accent-dim/60 border border-primary cursor-pointer transition-colors duration-150 text-left"
    : "group relative flex flex-col gap-1 p-4 rounded-lg bg-surface-container-low border border-transparent hover:border-border hover:bg-surface-container cursor-pointer transition-colors duration-150 text-left"
}
```

Selected left bar:

```tsx
{isSelected && (
  <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-primary rounded-l" />
)}
```

Selected icon color: `text-primary` instead of `text-accent-spore`.

Title hover: `group-hover:text-primary` instead of `group-hover:text-primary-fixed` (optional cleanup).

- [ ] **Step 3: Grep SearchPage for spore selection leftovers**

Run:

```bash
rg -n "accent-spore|0_0_15px|c4a35a|196,163,90" apps/desktop/src/pages/SearchPage.tsx || echo "CLEAN"
```

Expected: `CLEAN`.

- [ ] **Step 4: Build + commit (if git)**

```bash
cd /Users/tylerhughes/PlayingAround/MemoryOptimization/apps/desktop && npm run build
git add apps/desktop/src/pages/SearchPage.tsx
git commit -m "$(cat <<'EOF'
feat(desktop): Soft Electric search selection states
EOF
)"
```

---

### Task 5: Library density + radius

**Files:**
- Modify: `apps/desktop/src/pages/LibraryPage.tsx`

**Interfaces:**
- Consumes: `primary` / `primary-container` (already healthy=blue after Task 2)
- Produces: Consistent `rounded-lg` on inputs/rows; primary Register button `rounded-xl`; tighter stats via `min-w-[72px]` and `gap-md`

- [ ] **Step 1: Radius pass on controls**

On Library page interactive surfaces, prefer `rounded-lg` for:
- Add workspace toggle button
- Add-workspace panel container
- Path input
- Filter input
- Workspace rows

Register button:

```tsx
className="px-md py-sm bg-primary text-on-primary rounded-xl font-body-sm text-body-sm disabled:opacity-50 transition-colors duration-150"
```

(Use solid `bg-primary` / `text-on-primary` instead of `primary-container` for the primary action.)

- [ ] **Step 2: Tighten stats columns**

In each workspace row stats block, change `min-w-[80px]` → `min-w-[72px]` and outer `gap-lg` → `gap-md` where the three metric columns sit.

- [ ] **Step 3: Soften row hover**

Change row hover from `hover:border-outline` to surface raise only:

```tsx
className={`group flex items-center gap-md p-md bg-surface-container-lowest border border-border rounded-lg hover:bg-surface-container-low transition-colors duration-150 cursor-pointer relative overflow-hidden ${
  ws.status === "idle" ? "opacity-70 hover:opacity-100" : ""
}`}
```

- [ ] **Step 4: Build + commit (if git)**

```bash
cd /Users/tylerhughes/PlayingAround/MemoryOptimization/apps/desktop && npm run build
git add apps/desktop/src/pages/LibraryPage.tsx
git commit -m "$(cat <<'EOF'
feat(desktop): polish Library for Soft Electric density
EOF
)"
```

---

### Task 6: Vault — remove hardcoded green

**Files:**
- Modify: `apps/desktop/src/pages/VaultPage.tsx`

**Interfaces:**
- Consumes: `accent-hypha` / `primary` (now blue)
- Produces: SVG node fill uses `currentColor` or `#6ec8ff`; no `#9cd2ba` literal

- [ ] **Step 1: Replace SVG fill**

Find `fill="#9cd2ba"` (mini graph / node decoration) and change to:

```tsx
<circle cx="50" cy="50" fill="#6ec8ff" r="4" />
```

(or `fill="currentColor"` with `className="text-primary"` on the parent SVG if structure allows).

- [ ] **Step 2: Radius consistency**

Where note list / editor chrome use bare `rounded`, prefer `rounded-lg` on panels and `rounded-xl` only if a primary CTA exists on this page.

Backlink cards: keep `hover:border-accent-hypha` (now blue) — no class rename required.

- [ ] **Step 3: Grep Vault for old green**

Run:

```bash
rg -n "9cd2ba" apps/desktop/src/pages/VaultPage.tsx || echo "CLEAN"
```

Expected: `CLEAN`.

- [ ] **Step 4: Build + commit (if git)**

```bash
cd /Users/tylerhughes/PlayingAround/MemoryOptimization/apps/desktop && npm run build
git add apps/desktop/src/pages/VaultPage.tsx
git commit -m "$(cat <<'EOF'
feat(desktop): Soft Electric Vault accents
EOF
)"
```

---

### Task 7: Index + Settings polish

**Files:**
- Modify: `apps/desktop/src/pages/IndexPage.tsx`
- Modify: `apps/desktop/src/pages/SettingsPage.tsx`

**Interfaces:**
- Consumes: `primary` for progress/focus (already blue after Task 2)
- Produces: `rounded-lg` / `rounded-xl` on panels and primary Save; Settings inputs `focus:border-primary`

- [ ] **Step 1: IndexPage radius**

Replace `rounded-DEFAULT` with `rounded-lg` on sections, inputs, and secondary buttons in `IndexPage.tsx`. Progress bar track/fill already uses `bg-primary` — leave widths/logic unchanged.

Remove decorative `animate-pulse` on the Sync Failed error card if it feels “glow-like”; keep error styling with `border-danger/30` only:

```tsx
className="bg-surface-container-lowest border border-danger/30 rounded-lg p-md relative flex items-start gap-sm"
```

- [ ] **Step 2: SettingsPage focus + Save button**

1. Vault path and other inputs: `focus:border-outline` → `focus:border-primary`, `rounded` → `rounded-lg`
2. Trust panel: `rounded-DEFAULT` → `rounded-lg`
3. Save changes button:

```tsx
className="px-xl h-10 rounded-xl bg-primary text-on-primary font-label-md text-label-md hover:brightness-110 transition-all duration-150 flex items-center gap-sm"
```

(Replace `text-on-primary-fixed` / `hover:bg-opacity-90` with `text-on-primary`.)

4. Trust pulse dot: keep `bg-primary` (now blue); optional: remove `animate-pulse` for softer electric (preferred: remove pulse).

- [ ] **Step 3: Build + commit (if git)**

```bash
cd /Users/tylerhughes/PlayingAround/MemoryOptimization/apps/desktop && npm run build
git add apps/desktop/src/pages/IndexPage.tsx apps/desktop/src/pages/SettingsPage.tsx
git commit -m "$(cat <<'EOF'
feat(desktop): Soft Electric Index and Settings polish
EOF
)"
```

---

### Task 8: VS Code panel token sync + DESIGN.md

**Files:**
- Modify: `apps/vscode/media/panel.css`
- Modify: `_bmad-output/planning-artifacts/ux-designs/ux-mycelium-2026-07-25/DESIGN.md`

**Interfaces:**
- Consumes: Soft Electric primary `#6EC8FF`, container `#3A7FA8`
- Produces: Editor panel matches desktop accent; DESIGN.md documents Soft Electric as current system

- [ ] **Step 1: Update VS Code panel CSS vars**

In `apps/vscode/media/panel.css` `:root`:

```css
  --primary: #6ec8ff;
```

Find any hardcoded `#679b86` (button background) and set to `#3a7fa8`.

- [ ] **Step 2: Update DESIGN.md frontmatter colors**

In `_bmad-output/planning-artifacts/ux-designs/ux-mycelium-2026-07-25/DESIGN.md`, set:

```yaml
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
```

Update prose: brand style **Soft Electric Instrument**; primary actions/healthy = electric blue; spore = indexing/warn only; selection = blue not spore. Note Stitch HTML under `mockups/` is historical until regenerated.

- [ ] **Step 3: Repo-wide green audit (source only)**

Run:

```bash
cd /Users/tylerhughes/PlayingAround/MemoryOptimization
rg -n "9cd2ba|b7eed6|679b86" \
  apps/desktop/src \
  packages/ui/src \
  apps/vscode/media \
  --glob '!**/stitch/**' \
  --glob '!**/node_modules/**' \
  --glob '!**/dist/**' \
  || echo "CLEAN"
```

Expected: `CLEAN`. (Stitch HTML and historical mockups may still contain green — leave them.)

- [ ] **Step 4: Final desktop build + visual smoke**

```bash
cd /Users/tylerhughes/PlayingAround/MemoryOptimization/apps/desktop && npm run build && npm run dev
```

Manually spot-check: Library, Search (select a row), Vault, Index, Settings — accent is light blue, no green, no glow shadows.

- [ ] **Step 5: Commit (if git)**

```bash
git add apps/vscode/media/panel.css \
  _bmad-output/planning-artifacts/ux-designs/ux-mycelium-2026-07-25/DESIGN.md
git commit -m "$(cat <<'EOF'
docs(ui): Soft Electric DESIGN.md and VS Code panel tokens
EOF
)"
```

---

## Spec coverage checklist

| Spec requirement | Task |
|---|---|
| Primary `#6EC8FF` replaces green | 1, 2 |
| Accent muted/dim tokens | 1, 2 |
| Secondary gold for indexing only | 1, 4 (selection not gold) |
| No glow | 4 (remove shadow), 7 (error pulse) |
| Radius 8px / buttons 10px | 2, 3, 5–7 |
| AppShell ~176px, New note, header cleanup | 3 |
| Library / Search / Index / Vault / Settings | 4–7 |
| `@mycelium/ui` theme | 1 |
| DESIGN.md sync | 8 |
| VS Code panel (free token sync) | 8 |
| Stitch HTML out of scope | Explicitly skipped |

## Self-review notes

- No TBD/placeholder steps; hex values and class strings are explicit.
- Token names preserved (`accent-hypha`) with new values — pages using `border-accent-hypha` pick up blue without renames.
- Selection accent deliberately moved off `accent-spore` in Search (Task 4) to match spec.
- Commits are conditional on git existing.
