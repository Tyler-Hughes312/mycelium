---
name: Mycelium
status: final
sources:
  - _bmad-output/planning-artifacts/prds/prd-mycelium-2026-07-25/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-mycelium-2026-07-25/ARCHITECTURE-SPINE.md
updated: 2026-07-25
stitch_project: projects/1582993350217593804
---

# Mycelium — Experience Spine

## Foundation

**Form-factor:** multi-surface desktop product.
- **Desktop App** (Tauri 2 + React) — primary human UI: workspaces, index, search, Thinking Vault, settings.
- **VS Code / Cursor Side Panel** — secondary: focus Context Packet + quick Note create.
- **MCP** — agent surface (no visual UX beyond docs).

**UI system:** React + shared `@mycelium/ui`. Visual identity owned by `DESIGN.md` (Stitch-produced). Desktop window ~1080×720 minimum; Side Panel ~320–360px wide.

**Product rule:** one local Core Service; Desktop and Editor never diverge in data.

## Information Architecture

| Surface | App | Reached from | Purpose |
|---|---|---|---|
| Home / Library | Desktop | App launch | Workspace list, health, jump to Search |
| Index Console | Desktop | Home “Add / Index” | Register repo, progress, errors, cancel |
| Search | Desktop | Home search / ⌘K | RAG Query → ranked Context Packet |
| Result Detail | Desktop | Search row | Symbol/Commit/Note/File detail + actions |
| Vault / Note | Desktop | Nav “Vault” / New Note | Markdown edit, wikilinks, backlinks |
| Settings / Privacy | Desktop | Nav gear | Paths, models, history depth, local-only trust |
| Focus Panel | Editor | Editor open | Context for current file/symbol |
| Quick Note | Editor | Panel CTA | Create Note linked to current Symbol |

Nav model (Desktop): persistent left rail — Library · Search · Vault · Settings. No account menu.

## Voice and Tone

| Do | Don't |
|---|---|
| “Index paused. Resume when ready.” | “Oops! Something went wrong 😅” |
| “3 related notes · 2 commits” | “We found some amazing matches for you!” |
| “Stays on this machine.” | “Your data is important to us.” |
| “Core offline — Retry” | Blank panel with spinner forever |
| Paths and SHAs in monospace | Marketing exclamation points |

## Component Patterns

| Component | Use | Behavioral rules |
|---|---|---|
| Provenance chip | Search, Panel | Types: Symbol · Commit · Note · File. Click filters or reveals type legend. Never more than one primary chip per row. |
| Result row | Search, Panel | Title + one-line snippet + path/mono meta + chips. Entire row clickable. Hover reveals secondary actions (Open · Copy path · Link note). Max default list = 10. |
| Status pill | Home, Panel, Settings | Core: Connected / Offline / Indexing. Index: Idle / Running / Error. |
| Index progress | Index Console | Determinate when % known; else activity + counts (files, commits). Cancel always available. |
| Note editor | Vault | Plain markdown; `[[wikilink]]` autocomplete; backlinks pane right or below. Save writes disk immediately (debounce OK). |
| Trust panel | Settings | Static local-first facts + link to open data directory. No telemetry toggle default-on. |
| Empty state | Any | One sentence + one primary action. No illustration required. |

## State Patterns

| State | Surface | Treatment |
|---|---|---|
| Cold launch | Home | Skeleton workspace rows → populate; if Core down, full-page “Core offline” with Retry / Open logs |
| No workspaces | Home | “Add a repo to grow the graph.” Primary: Add workspace |
| Indexing | Index / Home | Live progress; Search still available on prior index with “Updating…” banner |
| Empty search | Search | “No matches. Try a Symbol name, or open Vault to capture a Note.” |
| Core offline | Editor Panel | Status pill Offline + Retry; do not show stale ranked results as live |
| Unresolved wikilink | Vault | Distinct muted style; click offers create-note |
| Huge repo | Index | Warn before deep history; allow depth limit change |

## Interaction Primitives

**Desktop**
- `⌘K` — focus Search (or command palette if unified later)
- `⌘N` — New Note (Vault context)
- `⌘,` — Settings
- `Esc` — close detail / clear search focus
- Arrow keys move result selection; `Enter` opens

**Editor Panel**
- Auto-refresh on active editor change (debounced)
- Manual refresh command
- `Mycelium: New Note` command

**Banned in v0:** infinite scroll result lists, modal stacks >1, account signup walls, graph-viz as primary nav.

## Accessibility Floor

- WCAG 2.2 AA on Desktop webview and extension webview
- Visible focus rings on all controls
- Status changes announced via `aria-live` (Core offline, index complete)
- Don’t rely on color alone for provenance — chip includes text label
- `prefers-reduced-motion`: disable non-essential transitions

## Key Flows

### KF-1 — First useful Context (UJ-1 / UJ-4)
1. Launch Desktop → Core Connected  
2. Add Workspace Repo → Initial Index with progress  
3. Open Search → query past decision → open Commit/Note result  
**Climax:** user finds forgotten Context without leaving Desktop.

### KF-2 — Think in Vault (UJ-2)
1. From Search or Editor, create Note linked to Symbol  
2. Edit markdown with `[[links]]`  
3. Backlinks show; Search returns Note  
**Climax:** thinking and code share one graph.

### KF-3 — Code with Side Panel (UJ-1)
1. Open file in Cursor  
2. Panel shows Focus Context Packet  
3. Click result or New Note  
**Climax:** useful Context appears while coding.

### KF-4 — Agent recall (UJ-3)
Out of visual scope; MCP uses same Search/Focus APIs. Desktop Settings may show “MCP connected” later — optional v0.

## Inspiration & Anti-patterns

**Inspiration:** Linear density, Obsidian vault honesty, Raycast calm focus.  
**Anti-patterns:** Notion template galleries, purple AI SaaS marketing UI, graph toys as home screen.

## Open Items

- Exact Stitch visual system → finalize DESIGN.md  
- Whether Desktop Search and ⌘K are the same surface  
- Reveal-in-Finder vs Open-in-Editor defaults per result type
