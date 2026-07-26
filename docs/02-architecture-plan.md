# Architecture Plan

## 1. High-Level System

Two deployable pieces, both talking to a shared "core" service:

```
+-------------------+      +--------------------+
|  Editor Bridge     | <--> |  Core Service       |
|  (VS Code / Claude |      |  (local process or  |
|   Code / JetBrains |      |   self-hosted /      |
|   extension)        |      |   hosted server)     |
+-------------------+      +--------------------+
                                    |
                     +--------------+---------------+
                     |                              |
             Graph Store (embeddings +        Optional: Team Sync
             metadata, local by default)      Layer (server-only)
```

- **Core Service**: the actual brain — graph builder, retrieval, ranking.
  Runs as a local process for a solo dev; runs as a shared container/server
  for a team. Same codebase, different deployment mode.
- **Editor Bridge**: thin extension per editor (VS Code, JetBrains, Claude
  Code) that just pings the local core service's API and renders results.
  This is intentionally "dumb" — all the intelligence lives in the core
  service so you're not rebuilding logic per editor.
- **Graph Store**: embeddings + metadata (files, commits, notes, links).
  Local by default (e.g., a lightweight embedded vector store). Optional
  sync layer for teams.

## 2. Core Components

### 2.1 Ingestion / Graph Builder
Responsible for turning raw repo data into graph nodes and edges.

Inputs:
- Git history (commits, diffs, authorship, timestamps)
- File/function structure (via language-aware parsing — tree-sitter is a
  strong default here since it supports most languages with one library)
- Manually authored notes (Obsidian-style, markdown, user-linked)
- (Later) PR descriptions, Slack/ticket mentions of specific files/functions

Two-speed design:
- **Cheap, continuous pass**: on every commit/edit, update embeddings for
  changed files/functions and add lightweight graph edges (e.g., "this
  function was touched in the same commit as that one").
- **Expensive, occasional pass**: periodically (or on-demand) run an LLM
  pass over larger chunks of the repo to produce higher-level structural
  summaries — "this is the auth service, it depends on the session store."
  This is slow and costly, so it should run rarely (e.g., nightly, or
  triggered manually), not on every keystroke.

### 2.2 Embedding / Retrieval Layer
- Use a small, local code-aware embedding model for the continuous pass
  (fast, cheap, can run on a laptop, no external API calls required for the
  personal tier).
- Store vectors + metadata in a lightweight local vector store.
- Retrieval query: given "current file + function," return top-k related
  nodes by a blend of (a) vector similarity, (b) graph proximity/explicit
  links, (c) recency, (d) a learned "was this actually clicked before"
  signal.

### 2.3 Orchestration / Ranking Layer
This is the actual product intelligence — deciding *what* to surface *when*.

Signals it combines:
1. Current file + function context (what the dev is looking at right now)
2. Recent git history on that file (who touched it last, and why)
3. Related notes explicitly linked in the graph
4. Related discussion (Slack/ticket mentions — later integration)
5. Feedback signal: has this piece of context been surfaced before, and was
   it actually opened/used? (this is what prevents the tool from becoming
   noisy — a naive version floods the user with "similar" results and gets
   ignored; the learned click-through signal is what keeps it sharp)

Output: a ranked, small list of relevant context, not a firehose.

### 2.4 Generation Layer (LLM, bring-your-own-key)
- Not required to run the retrieval/graph parts of the product.
- Used only when the user asks for something generative: "explain this,"
  "write this similar to what I did before," "summarize this repo."
- Bring-your-own-API-key model (Claude, OpenAI, etc.) for the personal tier,
  or point at a local model (e.g., via Ollama) for fully offline use.
- This keeps your hosting costs at ~$0 for the free tier — you're never
  paying for someone else's inference.

### 2.5 Team Sync Layer (paid, server-only)
- Only exists in the team/enterprise deployment mode.
- Merges multiple developers' local graphs into a shared graph: shared
  conventions, cross-service ownership, org-wide notes.
- Needs real infrastructure decisions here: conflict resolution when two
  people's graphs disagree, access control (who can see what), and sync
  frequency.
- This is the part that justifies a server and justifies pricing — it's
  doing something a local-only tool structurally cannot do.

## 3. Data Flow (personal tier, concrete walkthrough)

1. Dev opens a file in their editor.
2. Editor Bridge sends "current file + cursor context" to the local Core
   Service.
3. Core Service queries the Graph Store: vector search + graph traversal
   from that file/function.
4. Orchestration layer ranks results (recency, link strength, past
   usefulness).
5. Editor Bridge renders a small side panel: "related commits," "your past
   notes," "similar code elsewhere in this repo."
6. Dev can click through, or add a new note right there, which becomes a
   new graph node/edge instantly.
7. In the background, the continuous ingestion pass keeps updating
   embeddings as commits happen.

## 4. Tech Stack (suggested starting points, not final)

- **Graph builder / core service**: whatever language you're fastest in for
  a backend service — this needs to be a real, testable service, not a
  script.
- **Code parsing**: tree-sitter (broad language support, mature, fast).
- **Embeddings**: a small local/open embedding model suited for code (this
  needs an actual eval pass — don't assume a generic text embedding model
  performs well on code without checking).
- **Vector store**: a lightweight, embeddable vector database that can run
  locally without a separate server process for the personal tier, and can
  be swapped for a hosted vector DB in the team tier.
- **Editor bridge**: VS Code extension API to start (largest addressable
  audience among engineers using AI coding tools); Claude Code integration
  as a close second given your own workflow; JetBrains later.
- **Packaging for self-host**: Docker container for the team/self-hosted
  server, so a solo dev or small team can run the whole thing with one
  command and zero cloud setup.
- **Hosted tier infra**: only needed once you're actually selling the hosted
  convenience tier — don't build this until the self-hosted version proves
  the core loop works.

## 5. Privacy / Trust Architecture

Given developers are being asked to point this at their entire codebase,
architecture needs to make the privacy story obviously true, not just
claimed:

- Personal tier: 100% local. No network calls except the user's own
  optional LLM API key. This should be verifiable (open source core helps
  here — people can read the code).
- Team tier: explicit opt-in sync, scoped to what's shared, with access
  control per repo/graph segment.
- Enterprise: self-hosted by default, so nothing leaves their
  infrastructure at all.

## 6. What NOT to build early

- Full multi-source RAG (Slack + tickets + code) — start with git + code +
  manual notes only. Multi-source ingestion is a team/enterprise-tier
  feature, not an MVP feature.
- A hosted inference layer — bring-your-own-key avoids this cost and
  complexity entirely at first.
- Cross-team/cross-org graph merging — solve single-team sync first.
- Heavy graph visualization UI — the ranking/surfacing UX matters far more
  early on than a fancy visual graph explorer (Obsidian already proved the
  graph-view is a "nice to have," not the core value).
