# Build Plan

## 1. Guiding Principle

Build the smallest version that proves one loop: *the tool surfaces
genuinely useful old context at the right moment, without the user manually
searching for it.* Everything else — team sync, Slack integration, fancy
graph UI, billing — comes after that loop is proven on your own daily use.

## 2. MVP Scope (v0)

Three pieces only:

1. **Local ingestion**: watches a codebase, builds a lightweight graph from
   git history and file/function relationships. No Slack, no tickets, no
   team sync yet.
2. **Editor side panel**: a simple VS Code (or Claude Code) extension that
   shows relevant past commits and your own manual notes when you open a
   file.
3. **Manual notes**: Obsidian-style notes that link to specific files or
   functions — basically backlinks, scoped to code.

This is realistically buildable solo in a few months, and it already tests
the core hypothesis: does surfacing old context actually save time.

**Explicit non-goals for v0**: team accounts, billing, hosted server,
Slack/ticket ingestion, fancy graph visualization, multi-editor support.

## 3. Using Agent-Assisted Development (dogfooding the idea while building it)

You've already built pieces of this before across past projects — a git
history parser, maybe a graph/vector setup, an extension skeleton, an auth
flow. The build plan should literally use the product's own idea to
accelerate its own construction:

### Step 1 — Inventory pass
Use a coding agent (Claude Code or similar) pointed at your GitHub account
to scan past repos for reusable pieces. Ask it to summarize what each repo
does and flag anything reusable: file watchers, embedding/vector setups,
extension scaffolding, auth flows, etc. Agents are genuinely good at this
kind of "code archaeology" — summarizing unfamiliar or half-forgotten repos.

### Step 2 — Build a context store from that inventory
Turn the useful pieces from Step 1 into an embedding index (a rough,
hand-rolled version of the product itself) so that later, when an agent asks
"have I built a file watcher before," it gets back actual code, not a guess.
This is worth doing even before the "real" product exists — it directly
speeds up your own build and it's a genuine proof of concept.

### Step 3 — Agent-assisted component build
Feed the MVP spec (Section 2) to a coding agent. For each component, have
the agent first query your Step 2 context store for relevant old code,
adapt rather than write from scratch, then you review before merging. Treat
the agent as a fast first-drafter, not an autonomous shipper — review every
component before it lands.

## 4. Build Sequence (concrete order)

1. **Repo inventory + personal context store** (Step 1–2 above). This both
   accelerates everything after it and is a working micro-version of the
   product's core mechanic.
2. **Git history parser**: extracts commits, diffs, authorship, timestamps
   from a target repo.
3. **Code structural parser**: file/function boundaries via tree-sitter (or
   similar), so the graph has real nodes to attach context to, not just
   whole files.
4. **Embedding pipeline**: turn parsed functions/commits into vectors,
   store in a local embeddable vector store.
5. **Graph store**: lightweight schema connecting files, functions, commits,
   and notes with typed edges (e.g., "modified in," "related to,"
   "explained by").
6. **Retrieval + ranking logic**: given a current file/function, return a
   small ranked list of relevant nodes (recency + link strength first pass;
   click-through learning can come later).
7. **Manual note-taking**: UI/API to add a note and link it to a
   file/function — this is the part that most directly resembles Obsidian.
8. **Editor bridge (VS Code first)**: side panel that calls the local core
   service and renders ranked results + notes.
9. **Dogfood loop**: use it daily on your own repos (including the ones
   from Step 1) for at least a few weeks before showing anyone else.
10. **Polish for public release**: README, install script, demo video,
    open-source licensing decision.

## 5. Post-MVP Roadmap

### v1 — Public open-source launch
- Package as a one-command self-hosted setup (Docker) so anyone can try it
  in minutes.
- Public demo video showing one concrete "aha" retrieval moment.
- Show HN / Product Hunt / dev-Twitter launch.
- Build-in-public devlog throughout, not just at launch.

### v2 — Team layer
- Server component for shared/team graphs.
- Access control, sync/merge logic across multiple developers' graphs.
- This is the first genuinely paid feature — hosted convenience tier for
  teams who don't want to run their own server.

### v3 — Richer ingestion
- PR descriptions, Slack mentions, ticket references tied into the graph.
- LLM-based occasional structural passes ("this is the auth service, it
  depends on X") layered on top of the fast embedding-based retrieval.

### v4 — Enterprise
- Self-hosted at scale, SSO, audit logs, admin controls, private/offline
  model routing.
- Support SLAs, procurement-friendly packaging.

## 6. Success Checkpoints

- **Checkpoint 1**: You personally use it daily and it saves you real time
  finding old context — if this isn't true, nothing downstream matters.
- **Checkpoint 2**: A handful of external developers self-host it from the
  open-source repo without your help (proves the "zero-ops self-host" story
  actually works).
- **Checkpoint 3**: One of those individual users brings it to their team
  and asks about the shared/team layer (proves the free-to-paid motion).
- **Checkpoint 4**: A team actually pays for the hosted or enterprise tier.

## 7. Immediate Next Actions

1. Run the repo inventory pass (Section 3, Step 1) on your own GitHub —
   this is genuinely useful today, independent of anything else.
2. Pick the vector store and embedding model for the personal tier and do a
   quick eval on a real repo (yours) before committing.
3. Build the git history parser and structural parser — these are pure
   infrastructure with no ambiguity, good first real components.
4. Get the VS Code side panel showing *anything* end-to-end (even
   unranked, unfiltered results) as fast as possible — an ugly working loop
   beats a polished non-loop for validating the idea.
