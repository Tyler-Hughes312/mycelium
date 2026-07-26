---
title: Mycelium
status: final
created: 2026-07-25
updated: 2026-07-25
change: desktop-app-v0
---

# PRD: Mycelium

## 0. Document Purpose

This PRD defines Mycelium MVP for planning and implementation (architecture, epics, stories). It builds on `docs/01-business-plan.md`, `docs/02-architecture-plan.md`, `docs/03-build-plan.md`, and the product brief. Features use globally numbered FRs; assumptions are tagged inline and indexed in §9. Technical mechanism choices live in `addendum.md` and the architecture spine.

## 1. Vision

Mycelium is a self-building second brain for software engineers. It automatically grows a living Knowledge Graph from a developer’s code, git history, and personal notes — then surfaces the right Context at the right moment inside the editor and AI agents they already use.

As coding agents get faster and cheaper, the bottleneck shifts from “can the model write code” to “does the model have the right Context.” Mycelium is that Context Layer for an individual developer first: local RAG, local embeddings, and an Obsidian-like Thinking Vault — without requiring cloud upload by default.

## 2. Target User

### 2.1 Jobs To Be Done

- When I’m deep in a file, help me recover *why* this code is weird without spelunking git blame manually.
- When my agent starts a new session, give it durable project memory grounded in code structure and my notes — not sticky notes I forgot to update.
- When I’m thinking through a design, let me write like Obsidian (wikilinks, backlinks) *linked to real code entities*.
- When I install a local tool, keep my repos on my machine; zero trust theater.

### 2.2 Non-Users (v1)

- Teams needing shared multi-dev sync out of the box
- Enterprises requiring SSO/audit in v0
- Developers unwilling to run a local process or index a repo once
- Users seeking a hosted-only SaaS memory product

### 2.3 Key User Journeys

- **UJ-1. Alex indexes a repo and gets useful Context in minutes.**
  - **Persona + context:** Alex, senior IC, lives in Cursor/Claude Code, juggles 5 repos, hates re-explaining decisions to agents.
  - **Entry state:** Mycelium Core Service installed locally; no cloud account.
  - **Path:** Points Mycelium at a git repo → waits for Initial Index → opens a hot file in VS Code/Cursor → Side Panel shows related Commits, Symbols, and Notes.
  - **Climax:** One result explains a past decision Alex had forgotten; Alex opens it without searching.
  - **Resolution:** Repo stays Indexed; continuous updates run in background.
  - **Edge case:** Huge monorepo — indexing shows progress and remains interruptible; partial results still queryable.

- **UJ-2. Jordan writes a Thinking Vault note linked to a function.**
  - **Persona + context:** Jordan designs in markdown, wants Obsidian-style thinking tied to code.
  - **Entry state:** Repo Indexed; cursor inside `authenticate()`.
  - **Path:** Creates Note from Side Panel or vault → adds `[[wikilink]]` to Symbol → saves.
  - **Climax:** Backlinks show the Note when that Symbol is open; RAG query for “auth retry” returns the Note.
  - **Resolution:** Note is a first-class Graph Node linked to the Symbol.

- **UJ-3. Sam’s coding agent pulls Mycelium Context via MCP.**
  - **Persona + context:** Sam runs Claude Code / Cursor agent daily; wants automatic project memory.
  - **Entry state:** Core Service running; MCP Bridge configured.
  - **Path:** Agent asks “how did we handle rate limits before?” → MCP tool queries Mycelium → returns ranked Context Packet (Symbols, Commits, Notes).
  - **Climax:** Agent cites real prior code/notes instead of inventing.
  - **Resolution:** Same Graph Store as the Side Panel; no second memory silo.

- **UJ-4. Alex runs Mycelium Desktop as the home base.**
  - **Persona + context:** Same Alex; wants a full app for indexing, vault thinking, and search — not only a side panel.
  - **Entry state:** Desktop app installed; Core Service bundled or auto-started.
  - **Path:** Opens Desktop → adds Workspace Repo → watches Initial Index → searches RAG → browses/edits Thinking Vault → later codes in Cursor with Side Panel still live.
  - **Climax:** Finds a forgotten Note + related Commit in Desktop search without leaving the app.
  - **Resolution:** Desktop and Editor Bridge share one Core; no duplicate indexes.

## 3. Glossary

- **Mycelium** — The product: local Context Layer for developers.
- **Core Service** — Local process that owns ingestion, Graph Store, RAG, and ranking; single source of truth.
- **Editor Bridge** — Thin VS Code/Cursor extension that renders Context; no business logic beyond UX.
- **MCP Bridge** — Local Model Context Protocol server exposing Graph/RAG tools to AI agents.
- **Knowledge Graph (Graph)** — Nodes (Symbols, Files, Commits, Notes) and typed Edges connecting them.
- **Symbol** — Language-aware code entity (function, class, method, module) from structural parsing.
- **Commit Node** — Graph node representing a git commit with metadata and linked changed Symbols/Files.
- **Thinking Vault (Vault)** — On-disk markdown folder with wikilinks/backlinks; user’s second brain.
- **Note** — Markdown document in the Vault; may link to Symbols/Files/Commits.
- **Graph Store** — Local persistence for Graph metadata + vector index for embeddings.
- **Embedding** — Local vector representation of a chunk (Symbol, Note, Commit message/diff summary).
- **RAG Query** — Hybrid retrieval over Graph Store returning a ranked Context Packet.
- **Context Packet** — Small ranked list of Graph nodes + snippets for a query or current editor focus.
- **Side Panel** — Editor Bridge UI showing Context Packet for current File/Symbol.
- **Desktop App** — Native shell application for workspace management, indexing, RAG search, Thinking Vault, and settings.
- **Initial Index** — First full ingestion pass over a Workspace Repo.
- **Workspace Repo** — A git repository the user has registered with Mycelium.
- **Context Layer** — Product category: software that supplies durable Context to humans and agents.

## 4. Features

### 4.1 Workspace & Local Core

**Description:** User runs Mycelium entirely locally, registers Workspace Repos, and sees indexing status. Realizes UJ-1.

**Functional Requirements:**

#### FR-1: Install and run Core Service locally

Developer can install and start the Core Service on their machine without creating a cloud account.

**Consequences (testable):**
- Core Service binds to localhost by default.
- No outbound network is required for ingestion, Embedding, or RAG Query (except optional model download on first setup, clearly disclosed).

#### FR-2: Register a Workspace Repo

Developer can register a local git repository path as a Workspace Repo.

**Consequences (testable):**
- Invalid/non-git paths are rejected with a clear error.
- Registered path persists across Core Service restarts.

#### FR-3: Initial Index with progress

Developer can run Initial Index and observe progress (files/commits processed, ETA or percent).

**Consequences (testable):**
- Index can be cancelled mid-run without corrupting the Graph Store.
- After cancel or crash, re-run resumes or safely rebuilds without duplicate Node IDs for the same content hash. `[ASSUMPTION: resume via content-hash idempotency]`

#### FR-4: Continuous incremental update

After Initial Index, Core Service updates the Graph when files or git history change.

**Consequences (testable):**
- Editing a tracked file triggers re-embed of affected Symbols within a bounded delay. `[ASSUMPTION: ≤30s under normal laptop load for a single-file change]`
- New commits on the watched branch produce Commit Nodes linked to changed Files/Symbols.

### 4.2 Code & Git Ingestion

**Description:** Mycelium builds Graph structure from git and language-aware Symbols. Realizes UJ-1.

**Functional Requirements:**

#### FR-5: Ingest git history

Core Service creates Commit Nodes from git history (hash, author, timestamp, message, changed paths).

**Consequences (testable):**
- Configurable history depth for Initial Index (e.g. N commits or since date). `[ASSUMPTION: default last 500 commits]`
- Binary/large files can be skipped by policy.

#### FR-6: Parse Symbols with structural analysis

Core Service extracts Symbols from source files for supported languages.

**Consequences (testable):**
- At minimum supports Python, TypeScript/JavaScript, and Go in MVP. `[ASSUMPTION: tree-sitter grammars]`
- Unsupported files still exist as File nodes without Symbols.

#### FR-7: Auto-link co-change Edges

Core Service creates Edges between Symbols/Files that change together in the same Commit.

**Consequences (testable):**
- Opening a Symbol can retrieve co-changed Symbols via Graph traversal, not only Embedding similarity.

### 4.3 Local Embeddings & RAG

**Description:** Fully local Embedding pipeline and hybrid RAG Query. Realizes UJ-1, UJ-3.

**Functional Requirements:**

#### FR-8: Local Embedding generation

Core Service embeds Symbols, Notes, and Commit text using a local Embedding model with no API key required.

**Consequences (testable):**
- Embeddings are computed on-device.
- Model identity and download size are documented for the user before first download.

#### FR-9: Hybrid RAG Query

Developer or agent can run a natural-language RAG Query and receive a Context Packet.

**Consequences (testable):**
- Retrieval combines vector similarity and keyword/FTS signals. `[ASSUMPTION: RRF fusion]`
- Default top-k is small (≤10) to avoid firehose UX.

#### FR-10: Focus-based Context Packet

Given current File + optional Symbol (and cursor context), Core Service returns a ranked Context Packet.

**Consequences (testable):**
- Ranking uses at least: Embedding similarity, Graph proximity/explicit links, and recency.
- Results include typed provenance (Commit / Symbol / Note).

### 4.4 Thinking Vault (Obsidian-style second brain)

**Description:** Local markdown Vault for human thinking, linked into the Graph. Realizes UJ-2.

**Functional Requirements:**

#### FR-11: Vault on disk

Developer has a Thinking Vault as a folder of markdown files they can also edit in any editor.

**Consequences (testable):**
- Vault path is configurable.
- Files use plain markdown; no proprietary binary format.

#### FR-12: Wikilinks and backlinks

Developer can `[[wikilink]]` Notes and code entities; Mycelium resolves backlinks.

**Consequences (testable):**
- Creating `[[SymbolName]]` or a structured code link creates/updates an Edge when resolvable.
- Unresolved links are visible as unresolved, not silently dropped.

#### FR-13: Notes in RAG and Side Panel

Notes participate in RAG Query and Focus-based Context Packets (and Desktop search).

**Consequences (testable):**
- A Note linked to a Symbol appears when that Symbol is focused (explicit link boost).

### 4.5 Desktop App

**Description:** Full functional Desktop App as the human home base for Mycelium. Realizes UJ-4 (also supports UJ-1, UJ-2).

**Functional Requirements:**

#### FR-14: Desktop shell runs Core

Developer can launch the Desktop App and have the Core Service available (bundled or auto-started) without a separate manual terminal ritual for happy path.

**Consequences (testable):**
- Cold launch reaches a usable home screen with Core healthy (or clear recovery if Core fails).
- App remains local-first (FR-25).

#### FR-15: Desktop workspace & index console

Developer can register Workspace Repos, start/cancel Initial Index, and view progress/errors in the Desktop App.

**Consequences (testable):**
- Same workspace registration semantics as API (FR-2, FR-3).
- Progress UI updates without requiring the editor to be open.

#### FR-16: Desktop RAG search

Developer can run natural-language RAG Query from the Desktop App and open results (Files, Symbols, Commits, Notes).

**Consequences (testable):**
- Uses the same ranking contract as API Context Packets (FR-9).
- Results navigate to in-app detail or reveal-in-finder / open-in-editor where applicable.

#### FR-17: Desktop Thinking Vault

Developer can browse, create, and edit Notes in the Thinking Vault inside the Desktop App (markdown), including wikilinks/backlinks.

**Consequences (testable):**
- Edits write through to the on-disk Vault (FR-11).
- Backlinks panel or equivalent is available for the open Note (FR-12).

#### FR-18: Desktop settings & privacy

Developer can configure Vault path, embedding model, history depth, and see a clear “data stays local” privacy summary.

**Consequences (testable):**
- Changing Vault path is confirmed and reindexes Notes.
- No cloud account required.

### 4.6 Editor Bridge

**Description:** Thin Side Panel in VS Code/Cursor for in-flow Context. Realizes UJ-1, UJ-2. Complements Desktop App; does not replace it.

**Functional Requirements:**

#### FR-19: Side Panel Context

Developer sees Context Packet for the active editor File/Symbol.

**Consequences (testable):**
- Panel updates when switching files or selecting a recognized Symbol.
- Each result is clickable to open File at location, Commit detail, or Note.

#### FR-20: Editor status & refresh

Developer can see Core Service connection status and trigger refresh from the Editor Bridge.

**Consequences (testable):**
- Offline/unreachable Core Service shows a clear reconnect state (not a blank panel).
- Editor does not re-implement Desktop console features beyond focus Context + quick Note create.

#### FR-21: Create Note from editor context

Developer can create a Note pre-linked to the current File/Symbol from the Side Panel.

**Consequences (testable):**
- New Note appears in Vault and Desktop without a full reindex.

### 4.7 Agent / MCP Bridge

**Description:** AI agents query the same Graph via MCP. Realizes UJ-3.

**Functional Requirements:**

#### FR-22: MCP tools for recall

Agent can call MCP tools to search and fetch Context Packets from Mycelium.

**Consequences (testable):**
- At least: search/query, get-context-for-path, get-note, list-recent-commits-for-path.
- Responses are sized for agent Context windows (compact snippets + paths).

#### FR-23: Single store for human and agent

Desktop App, Editor Bridge, and MCP Bridge read the same Graph Store.

**Consequences (testable):**
- A Note created in the Vault (Desktop or Editor) is retrievable via MCP without a separate sync step beyond normal indexing.

### 4.8 Privacy & Trust

**Description:** Local-first guarantees are product requirements, not marketing. Cross-cutting for all UJs.

**Functional Requirements:**

#### FR-24: Local-by-default data plane

Workspace Repo contents and Vault stay on disk; Core Service does not upload code.

**Consequences (testable):**
- Network policy: no telemetry of source contents in MVP. `[ASSUMPTION: optional anonymous install ping deferred or off by default]`
- Optional generative LLM calls (if any) use user-provided keys and are explicit opt-in. `[NON-GOAL for MVP: built-in hosted inference]`

## 5. Non-Goals (Explicit)

- Team/org shared Graph sync, multi-user ACLs, billing
- Slack / Jira / Linear ingestion
- Fancy force-directed Graph visualization as primary UX
- Multi-editor bridges beyond VS Code/Cursor (JetBrains later)
- Hosted SaaS control plane
- Replacing the user’s LLM agent — Mycelium is Context Layer, not the agent
- Training or fine-tuning custom embedding models in MVP
- Cloning full Obsidian plugin ecosystem inside Desktop (v0 is operator + vault editor, not plugin marketplace)

## 6. MVP Scope

### 6.1 In Scope

- Local Core Service + Graph Store + local Embeddings + hybrid RAG
- Git + Symbol ingestion for a registered Workspace Repo
- Thinking Vault with wikilinks/backlinks linked to code
- **Full functional Desktop App** (workspaces, index, search, vault, settings)
- VS Code/Cursor Side Panel (focus Context + quick Note)
- MCP Bridge for AI agents
- Local-first privacy guarantees
- Shared UI component approach across Desktop + extension webview

### 6.2 Out of Scope for MVP

- Team sync / hosted tier (v2+)
- Slack/ticket ingestion (v3)
- Click-through learning ranker (v1.x — start with heuristic ranking)
- JetBrains bridge
- Enterprise SSO/audit
- LLM structural summarization pass (optional later; not required for MVP loop)
- Marketing website / account portal

## 7. Success Metrics

**Primary**
- **SM-1**: Time-to-first-useful-Context — median &lt; 15 minutes from Desktop install to a user-rated useful Desktop search or Side Panel / MCP result on a real repo. Validates FR-1–FR-17, FR-19, FR-22.
- **SM-2**: Weekly active retention among installers who complete Initial Index — ≥40% still query Mycelium in week 2 (dogfood + early external). Validates overall loop.

**Secondary**
- **SM-3**: Notes created per active user per week ≥1 among users who open Side Panel. Validates FR-11–FR-14.
- **SM-4**: MCP configured by ≥50% of AI-heavy early adopters who complete index. Validates FR-17–FR-18.

**Counter-metrics (do not optimize)**
- **SM-C1**: Raw nodes indexed / embedding count — optimizing this creates noise and slow indexes without usefulness.
- **SM-C2**: Panel result count — more results ≠ better; prefer small high-precision Context Packets.

## 8. Open Questions

1. Exact default Embedding model after laptop eval (Jina code vs Nomic text/code variants).
2. Default git history depth and monorepo performance budgets.
3. Vault UX: ship minimal built-in markdown preview vs. “bring your own Obsidian on the same folder.”
4. Licensing for open-core (Apache-2.0 vs MIT vs dual license for team features).
5. Whether Cursor-specific affordances beyond VS Code API are needed in MVP.

## 9. Assumptions Index

- Resume/idempotent indexing via content-hash — FR-3
- Incremental update ≤30s for single-file change — FR-4
- Default last 500 commits — FR-5
- tree-sitter for Symbol parsing; Py/TS/JS/Go first — FR-6
- RRF hybrid fusion — FR-9
- Telemetry off / no source upload — FR-24
- Core Service in Python 3.12; Desktop + Editor Bridge in TypeScript/React — architecture addendum
- Desktop shell: Tauri 2 pending confirm (vs Electron)
- jina-embeddings-v2-base-code as default laptop Embedding candidate pending eval
