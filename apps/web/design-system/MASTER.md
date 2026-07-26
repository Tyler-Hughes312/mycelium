# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Mycelium
**Generated:** 2026-07-26 16:40:45
**Category:** Developer Tool / IDE
**Design Dials:** Variance 7/10 (Balanced / Modern) | Motion 9/10 (Complex)

---

## Global Rules

### Color Palette

> **BRAND OVERRIDE (Mycelium product world):** the skill's green-SaaS defaults below were
> replaced with the locked Mycelium hexes from the marketing site design spec
> (`docs/superpowers/specs/2026-07-26-mycelium-marketing-site-design.md`). Primary/accent,
> background, and foreground are the source of truth for Hero / Get it / Footer chrome.

| Role | Hex | CSS Variable |
|------|-----|--------------|
| Primary | `#00d1b2` | `--color-primary` |
| On Primary | `#0F1113` | `--color-on-primary` |
| Secondary | `#334155` | `--color-secondary` |
| Accent/CTA | `#00d1b2` | `--color-accent` |
| Background | `#1c1f22` | `--color-background` |
| Foreground | `#f2f4f5` | `--color-foreground` |
| Muted | `#272F42` | `--color-muted` |
| Border | `#475569` | `--color-border` |
| Destructive | `#EF4444` | `--color-destructive` |
| Ring | `#00d1b2` | `--color-ring` |

**Color Notes:** Mycelium slate + teal product world (dark, technical, local-first).

#### Chapter washes (Capabilities / Setup only)

These are **not** global tokens — they're vivid poster-panel washes reserved for the
"chapter explosion" sections (Capabilities and Setup) per the design spec's hybrid
visual direction. Hero, Get it, and Footer stay in the slate/teal product world above.

| Wash | Hex | Used In |
|------|-----|---------|
| Magenta | `#E83A7A` | Capabilities cards (e.g. Library) |
| Sage | `#7CB69A` | Capabilities cards (e.g. Index) |
| Violet | `#7B6CF6` | Capabilities cards (e.g. Search) |

Setup chapter uses high-contrast slate + teal accents (not violet washes).

Teal (`#00d1b2`) remains the signature accent even inside vivid chapters — it should
read as a through-line connecting the calm product world to the vivid chapters, not be
replaced by the washes.

### Typography

- **Heading Font:** Inter
- **Body Font:** Inter
- **Mood:** dark, cinematic, technical, precision, clean, premium, developer, professional, high-end utility
- **Google Fonts:** [Inter + Inter](https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap)

**CSS Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
```

### Spacing Variables

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `4px` / `0.25rem` | Tight gaps |
| `--space-sm` | `8px` / `0.5rem` | Icon gaps, inline spacing |
| `--space-md` | `16px` / `1rem` | Standard padding |
| `--space-lg` | `24px` / `1.5rem` | Section padding |
| `--space-xl` | `32px` / `2rem` | Large gaps |
| `--space-2xl` | `48px` / `3rem` | Section margins |
| `--space-3xl` | `64px` / `4rem` | Hero padding |

### Shadow Depths

| Level | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle lift |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | Cards, buttons |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Modals, dropdowns |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.15)` | Hero images, featured cards |

---

## Component Specs

### Buttons

```css
/* Primary Button */
.btn-primary {
  background: #00d1b2;
  color: #0F1113;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* Secondary Button */
.btn-secondary {
  background: transparent;
  color: #f2f4f5;
  border: 2px solid #00d1b2;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 200ms ease;
  cursor: pointer;
}
```

### Cards

```css
.card {
  background: #1c1f22;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow-md);
  transition: all 200ms ease;
  cursor: pointer;
}

.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
```

### Inputs

```css
.input {
  padding: 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 200ms ease;
}

.input:focus {
  border-color: #00d1b2;
  outline: none;
  box-shadow: 0 0 0 3px #00d1b220;
}
```

### Modals

```css
.modal-overlay {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 90%;
}
```

---

## Style Guidelines

**Style:** Zero Interface

**Keywords:** Minimal visible UI, voice-first, gesture-based, AI-driven, invisible controls, predictive, context-aware, ambient

**Best For:** Voice assistants, AI platforms, future-forward UX, smart home, contextual computing, ambient experiences

**Key Effects:** Voice recognition UI, gesture detection, AI predictions (smooth reveal), progressive disclosure, smart suggestions

### Page Pattern

**Pattern Name:** Horizontal Scroll Journey

- **Conversion Strategy:** Immersive product discovery. High engagement. Keep navigation visible.
- **CTA Placement:** Floating Sticky CTA or End of Horizontal Track
- **Section Order:** 1. Intro (Vertical), 2. The Journey (Horizontal Track), 3. Detail Reveal, 4. Vertical Footer

---

## Motion

**Scroll Reveal** (Complex) — Trigger: scroll (continuous scrub) | Duration: tied to scroll position | Easing: `none (scrub-driven)`

```js
gsap.timeline({ scrollTrigger: { trigger: section, start: 'top top', end: '+=150%', scrub: 1, pin: true } }).from('.headline', { opacity: 0, y: 40 }).to('.bg-layer', { yPercent: -20 }, '<');
```

**Framework notes:** Pinning needs the section to have deterministic height; recalc ScrollTrigger.refresh() after images/fonts load

- ✅ Use scrub: true or a small number (0.5-1.5) instead of instant jumps so it feels tied to the scrollbar
- ❌ Don't pin more than 1-2 sections per page; excessive pinning fights native scroll feel and hurts mobile UX
- ⚡ Pinning forces layout reflow; test on mid-tier mobile devices, not just desktop

---

## Anti-Patterns (Do NOT Use)

- ❌ Light mode default
- ❌ Slow performance

### Additional Forbidden Patterns

- ❌ **Emojis as icons** — Use SVG icons (Heroicons, Lucide, Simple Icons)
- ❌ **Missing cursor:pointer** — All clickable elements must have cursor:pointer
- ❌ **Layout-shifting hovers** — Avoid scale transforms that shift layout
- ❌ **Low contrast text** — Maintain 4.5:1 minimum contrast ratio
- ❌ **Instant state changes** — Always use transitions (150-300ms)
- ❌ **Invisible focus states** — Focus states must be visible for a11y

---

## Pre-Delivery Checklist

Before delivering any UI code, verify:

- [ ] No emojis used as icons (use SVG instead)
- [ ] All icons from consistent icon set (Heroicons/Lucide)
- [ ] `cursor-pointer` on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard navigation
- [ ] `prefers-reduced-motion` respected
- [ ] Responsive: 375px, 768px, 1024px, 1440px
- [ ] No content hidden behind fixed navbars
- [ ] No horizontal scroll on mobile
