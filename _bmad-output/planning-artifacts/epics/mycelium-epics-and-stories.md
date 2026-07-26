---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-mycelium-2026-07-25/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-mycelium-2026-07-25/ARCHITECTURE-SPINE.md
status: final
created: 2026-07-25
updated: 2026-07-25
---

# Mycelium - Epic Breakdown

## Overview

Epic and story breakdown for Mycelium MVP, derived from the PRD (FR-1–FR-19) and Architecture Spine (AD-1–AD-8). Stories are ordered so each epic leaves a demonstrable increment toward the core loop: index → retrieve → note → surface in editor/agent.

## Requirements Inventory

### Functional Requirements

- FR-1 Install/run Core Service locally
- FR-2 Register Workspace Repo
- FR-3 Initial Index with progress
- FR-4 Continuous incremental update
- FR-5 Ingest git history
- FR-6 Parse Symbols
- FR-7 Auto-link co-change Edges
- FR-8 Local Embedding generation
- FR-9 Hybrid RAG Query
- FR-10 Focus-based Context Packet
- FR-11 Vault on disk
- FR-12 Wikilinks and backlinks
- FR-13 Create Note from editor context
- FR-14 Notes in RAG and Side Panel
- FR-15 Side Panel Context
- FR-16 Manual refresh and status
- FR-17 MCP tools for recall
- FR-18 Single store for human and agent
- FR-19 Local-by-default data plane

### NonFunctional Requirements

- Localhost-only default; no source upload (AD-2, FR-19)
- Top-k ≤ 10 Context Packets (AD-4)
- Idempotent indexing (AD-7)
- Bridges contain no ranking logic (AD-1, AD-6)
- Incremental single-file update target ≤30s (assumption)

### Additional Requirements

- Hexagonal package layout per Structural Seed
- Default Embedding candidate: jina-embeddings-v2-base-code (eval before pin)
- Supported languages MVP: Python, TS/JS, Go

### UX Design Requirements

- No formal UX spec yet; Side Panel = ranked list with typed provenance; Vault = plain markdown
- Status/reconnect states required (FR-16)

### FR Coverage Map

| FR | Epic |
|---|---|
| FR-1, FR-19 | E1 |
| FR-2, FR-3 | E1, E2 |
| FR-5, FR-6, FR-7 | E2 |
| FR-8, FR-9, FR-10 | E3 |
| FR-4 | E2, E3 |
| FR-11, FR-12, FR-13 | E4 |
| FR-14–FR-18 | E5 |
| FR-19–FR-21 | E6 |
| FR-22, FR-23 | E7 |
| FR-24 | E1, E5 |
| Polish / dogfood | E8 |

## Epic List

1. **E1 — Local Core Skeleton** — Runnable Core Service + config + privacy defaults
2. **E2 — Ingest Code & Git into Graph** — Workspace registration, git/Symbol ingestion, co-change Edges
3. **E3 — Local RAG** — Embeddings, hybrid search, focus Context Packets
4. **E4 — Thinking Vault** — Markdown second brain with wikilinks into Graph
5. **E5 — Desktop App** — Tauri/React full console (workspaces, index, search, vault, settings)
6. **E6 — Editor Bridge** — VS Code/Cursor Side Panel (shared `@mycelium/ui`)
7. **E7 — MCP Bridge** — Agent access to the same store
8. **E8 — Dogfood & Launch Hardening** — Install path, docs, eval, demo readiness

---

## Epic 1: Local Core Skeleton

Establish a runnable local Core Service with hexagonal layout, config, and local-first defaults so later epics plug into stable ports.

### Story 1.1: Project scaffold and Core Service hello

As a developer,
I want a Mycelium repo with Python Core Service scaffolding,
So that subsequent features have a stable place to land.

**Acceptance Criteria:**

**Given** a clean checkout  
**When** I create the `mycelium/` package layout per architecture Structural Seed  
**Then** `core/`, `adapters/`, `bridges/` directories exist with empty ports interfaces  
**And** the project uses the existing `venv` / lockfile approach for Python 3.12

### Story 1.2: Localhost HTTP API health

As a developer,
I want a FastAPI health endpoint on localhost,
So that bridges can detect the Core Service.

**Acceptance Criteria:**

**Given** Core Service started  
**When** I `GET /health`  
**Then** I receive 200 with service version  
**And** the bind address defaults to `127.0.0.1` (AD-2)

### Story 1.3: Config + data directories

As an AI-heavy developer,
I want Mycelium config and data under well-known local paths,
So that my repos are not uploaded and state survives restart.

**Acceptance Criteria:**

**Given** first run  
**When** Core Service starts  
**Then** it creates `~/.mycelium/config.toml` (or documented equivalent) and a local data dir  
**And** config documents that network for code upload is disabled by default (FR-19)

---

## Epic 2: Ingest Code & Git into Graph

Register a repo and build Graph Nodes/Edges from git history and Symbols.

### Story 2.1: Register Workspace Repo

As a developer,
I want to register a local git repo path,
So that Mycelium knows what to index (FR-2).

**Acceptance Criteria:**

**Given** Core Service running  
**When** I `POST /workspaces` with a valid git path  
**Then** the workspace is persisted and listed via `GET /workspaces`  
**And** non-git paths return a structured error

### Story 2.2: Git history ingestion

As a developer,
I want Commit Nodes created from git history,
So that past decisions are queryable (FR-5).

**Acceptance Criteria:**

**Given** a registered Workspace Repo  
**When** I start Initial Index  
**Then** Commit Nodes exist for up to the configured history depth (default 500)  
**And** each Node stores hash, author, timestamp, message, changed paths

### Story 2.3: Symbol parsing (Py/TS/JS/Go)

As a developer,
I want Symbols extracted via structural parsing,
So that Context attaches to functions/classes, not only files (FR-6).

**Acceptance Criteria:**

**Given** source files in supported languages  
**When** index runs  
**Then** Symbol Nodes include path, name, start/end line  
**And** unsupported files still create File Nodes without Symbols

### Story 2.4: Co-change Edges + index progress

As a developer,
I want co-change links and visible index progress,
So that related code is graph-reachable and long indexes feel safe (FR-3, FR-7).

**Acceptance Criteria:**

**Given** an indexing run  
**When** two Symbols change in the same Commit  
**Then** a `co_changed` Edge exists between them  
**And** `GET /workspaces/{id}/index/status` reports progress and supports cancel without store corruption (AD-7)

### Story 2.5: Incremental file update hook

As a developer,
I want changed files re-ingested automatically,
So that the Graph stays fresh (FR-4).

**Acceptance Criteria:**

**Given** an Indexed workspace  
**When** I modify a tracked source file and save  
**Then** affected File/Symbol Nodes upsert within the performance target  
**And** Node IDs remain stable (AD-7)

---

## Epic 3: Local RAG

Embeddings and hybrid retrieval producing Context Packets.

### Story 3.1: Embedding adapter + model bootstrap

As a developer,
I want local Embeddings without an API key,
So that RAG works offline after model download (FR-8).

**Acceptance Criteria:**

**Given** first Embedding request  
**When** the model is missing  
**Then** Mycelium downloads/caches the configured model with a clear log/UI notice  
**And** subsequent embeds run fully offline

### Story 3.2: Embed Symbols and Commits

As a developer,
I want indexed content embedded into the vector store,
So that semantic search works.

**Acceptance Criteria:**

**Given** Symbol and Commit Nodes  
**When** embedding pass runs  
**Then** vectors exist in LanceDB (or chosen store) keyed by Node ID  
**And** re-embed on content hash change only

### Story 3.3: Hybrid RAG Query API

As an AI-heavy developer,
I want natural-language search over my Graph,
So that I can ask “how did we do X?” (FR-9).

**Acceptance Criteria:**

**Given** an Indexed workspace with embeddings  
**When** I `POST /query` with text  
**Then** I receive a Context Packet ≤10 results  
**And** results reflect fused vector + FTS ranking (AD-4) with typed provenance

### Story 3.4: Focus Context Packet API

As a developer,
I want Context for the current file/symbol,
So that the Side Panel has a backend (FR-10).

**Acceptance Criteria:**

**Given** path + optional symbol name/line  
**When** I `POST /context/focus`  
**Then** I receive a ranked Context Packet using similarity + graph proximity + recency  
**And** empty index returns an empty packet with a helpful reason code

---

## Epic 4: Thinking Vault

Obsidian-style markdown second brain linked into the Graph.

### Story 4.1: Vault path + Note file CRUD API

As a developer,
I want a plain markdown Vault on disk,
So that I can think in files I own (FR-11).

**Acceptance Criteria:**

**Given** configured Vault path  
**When** I create/update/delete a Note via API  
**Then** corresponding `.md` files change on disk  
**And** Notes are readable in any external editor

### Story 4.2: Wikilink parse + backlinks

As a developer,
I want `[[wikilinks]]` resolved to backlinks,
So that my Thinking Vault behaves like a second brain (FR-12).

**Acceptance Criteria:**

**Given** Note A links `[[Note B]]` and a resolvable Symbol link  
**When** Notes are Indexed  
**Then** Edges exist and backlink query returns A from B  
**And** unresolved links are flagged in API metadata

### Story 4.3: Embed Notes into RAG

As a developer,
I want Notes to appear in search and focus results,
So that thinking and code Context share one brain (FR-13).

**Acceptance Criteria:**

**Given** an Indexed Note mentioning a topic  
**When** I RAG Query that topic or focus a linked Symbol  
**Then** the Note appears in the Context Packet with Note provenance  
**And** explicit Symbol links boost rank versus pure similarity

---

## Epic 5: Desktop App

Full functional desktop console using shared UI kit. **Depends on UX spines + design AI handoff** before visual polish; API-driven skeleton can start earlier.

### Story 5.1: Tauri shell + Core lifecycle

As a developer,
I want Mycelium Desktop to launch and keep Core healthy,
So that I am not managing terminals (FR-14).

**Acceptance Criteria:**

**Given** Desktop installed on macOS  
**When** I open Mycelium  
**Then** Core starts or connects on localhost and home screen loads  
**And** Core failure shows recovery actions

### Story 5.2: Shared `@mycelium/ui` package

As a developer,
I want shared React components/tokens,
So that Desktop and the VS Code webview stay visually consistent (AD-9).

**Acceptance Criteria:**

**Given** the monorepo packages  
**When** Desktop and extension import `@mycelium/ui`  
**Then** core primitives (result row, status pill, note link chip) render identically  
**And** tokens match DESIGN.md once UX is finalized

### Story 5.3: Workspace & index console

As a developer,
I want to manage repos and indexing in Desktop,
So that setup does not require the editor (FR-15).

**Acceptance Criteria:**

**Given** Core healthy  
**When** I add a Workspace Repo and start Initial Index  
**Then** progress/errors display live  
**And** cancel works without corrupting the store

### Story 5.4: Desktop RAG search

As an AI-heavy developer,
I want full-app search,
So that I can explore Context outside the editor (FR-16).

**Acceptance Criteria:**

**Given** an Indexed workspace  
**When** I run a query in Desktop search  
**Then** a Context Packet renders with typed provenance  
**And** opening a result navigates to detail / file / note

### Story 5.5: Desktop Vault editor

As a developer,
I want to read/write Notes with backlinks in Desktop,
So that the second brain is first-class (FR-17).

**Acceptance Criteria:**

**Given** Vault path configured  
**When** I create and wikilink a Note  
**Then** files land on disk and backlinks resolve  
**And** the Note appears in subsequent search

### Story 5.6: Settings & privacy panel

As a privacy-conscious developer,
I want clear local-first settings,
So that I trust Mycelium with my repos (FR-18, FR-24).

**Acceptance Criteria:**

**Given** Settings open  
**When** I view privacy summary and change Vault path / history depth  
**Then** changes persist and are reflected in Core config  
**And** no cloud account is required

---

## Epic 6: Editor Bridge

VS Code/Cursor Side Panel consuming Core APIs and `@mycelium/ui`.

### Story 6.1: Extension skeleton + Core connection status

As a developer,
I want a VS Code extension that shows Core Service status,
So that I know Mycelium is alive (FR-20).

**Acceptance Criteria:**

**Given** extension installed  
**When** Core is up/down  
**Then** status bar or panel shows connected/disconnected  
**And** a command exists to retry connection

### Story 6.2: Side Panel Context Packet view

As a developer,
I want a Side Panel of ranked Context for the active editor,
So that useful history appears without searching (FR-19, UJ-1).

**Acceptance Criteria:**

**Given** Core connected and workspace Indexed  
**When** I open a file / select a Symbol  
**Then** the panel calls `/context/focus` and renders typed results via `@mycelium/ui`  
**And** clicking a result navigates to file location, Note, or Commit detail

### Story 6.3: Create Note from current Symbol

As a developer,
I want to capture a thought linked to the current Symbol,
So that my Vault grows from real work (FR-21, UJ-2).

**Acceptance Criteria:**

**Given** active Symbol in editor  
**When** I run “Mycelium: New Note”  
**Then** a Note file is created in the Vault pre-linked to that Symbol  
**And** Desktop and the panel both reflect the new Note after refresh

---

## Epic 7: MCP Bridge

Expose the same Graph to AI agents.

### Story 7.1: MCP server process wired to Core

As an AI-heavy developer,
I want an MCP server for Mycelium,
So that Cursor/Claude Code can call it (FR-22).

**Acceptance Criteria:**

**Given** Core Service running  
**When** MCP Bridge starts  
**Then** it registers tools against the same Core API/store (AD-3)  
**And** README documents client config snippets for Cursor and Claude Code

### Story 7.2: Recall tools (search, focus, note, commits)

As an agent,
I want compact recall tools,
So that I can pull Context Packets into a session (FR-22, FR-23, UJ-3).

**Acceptance Criteria:**

**Given** MCP connected  
**When** the agent calls search / focus-by-path / get-note / commits-for-path  
**Then** responses return compact snippets + paths suitable for context windows  
**And** a Note created via Desktop Vault is visible via MCP after index without a separate DB

---

## Epic 8: Dogfood & Launch Hardening

Make install and usefulness real for external AI-heavy developers.

### Story 8.1: One-command local install + README

As a new user,
I want a short install path for Desktop (+ optional extension),
So that I reach first Context in &lt;15 minutes (SM-1).

**Acceptance Criteria:**

**Given** a fresh machine with supported OS prerequisites  
**When** I follow README steps  
**Then** Desktop launches, indexes a sample/real repo, and search returns results  
**And** privacy local-first claims are stated upfront

### Story 8.2: Embedding model eval harness

As the maintainer,
I want a small eval on a real repo,
So that we pin Embedding defaults with evidence.

**Acceptance Criteria:**

**Given** a fixture repo + labeled queries  
**When** I run the eval script  
**Then** it reports hit-rate for candidate models  
**And** default model in config is set from the winner (or documented interim)

### Story 8.3: Demo script + dogfood checklist

As the maintainer,
I want a reproducible aha demo across Desktop + editor + MCP,
So that launch/content shows one visceral retrieval moment.

**Acceptance Criteria:**

**Given** a dogfood repo with planted Note + history  
**When** I follow the demo script  
**Then** Desktop search, Side Panel, and MCP each surface the planted Context  
**And** a checklist verifies FR coverage smoke tests for E1–E7
