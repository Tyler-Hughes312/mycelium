# Business Plan: [Working Title] — "Obsidian for Codebases"

## 1. Vision

A self-building second brain for software engineers. Where Obsidian requires
manual note-linking, this product automatically builds a living knowledge
graph from a developer's code, git history, and personal notes — then
surfaces the right context at the right moment, inside whatever editor or
agent workflow they already use.

The long-term thesis: as AI coding agents get faster and cheaper, the
bottleneck shifts from "can the model write code" to "does the model have
the right context." This product becomes the context layer — for a single
developer first, then for a whole engineering org.

## 2. Problem

- Engineers accumulate huge amounts of undocumented context: why a function
  is written a strange way, what an incident taught the team, which service
  owns an edge case, what was already tried and abandoned.
- This context lives in scattered places — Slack threads, closed PRs, one
  person's memory — and decays fast as people forget or leave.
- AI coding agents (Claude Code, Cursor, Copilot) are only as good as the
  context they're fed. Most teams feed them almost nothing beyond the current
  file, so agents re-solve solved problems and re-write existing utilities.
- Manual tools like Obsidian solve "personal knowledge management" but require
  constant manual linking — nobody has the discipline to do that for a fast-
  moving codebase.

## 3. Product Layers

### Layer 1 — Personal Local Graph (individual devs)
- Runs locally, scoped to one developer's own repos, notes, and history.
- Auto-builds a graph from git history, commit messages, function-level
  diffs, and manually added notes (Obsidian-style backlinks, but scoped to
  code).
- Uses lightweight local embeddings for instant retrieval — no LLM required
  to run it day to day.
- Free forever. This is the adoption engine, not the revenue engine.

### Layer 2 — Team / Org Graph (paid)
- Aggregates context across multiple developers' work: shared conventions,
  cross-service dependencies, institutional knowledge that outlives any one
  engineer.
- Requires a server component (self-hosted container or hosted-by-us).
- This is where the willingness to pay lives — it solves a team-scale pain
  (onboarding, knowledge loss on attrition, duplicate work) that no individual
  tool touches.

### Layer 3 — Enterprise (paid, higher tier)
- Self-hosted on the customer's own infrastructure for security/compliance.
- SSO, audit logs, admin controls, private model routing (bring-your-own
  LLM key or fully offline via local models).
- Flat license or premium per-seat pricing.

## 4. Business Model

| Tier | Who | What they get | Price |
|---|---|---|---|
| Free / Local | Solo devs | Personal graph, local embeddings, manual notes, open-source core | $0 |
| Self-Hosted Team | Small teams, privacy-conscious devs | Team graph, run-your-own-container (Docker), no vendor lock-in | Free (open source) or low flat fee |
| Hosted Team | Teams who don't want ops overhead | We host the team graph, sync, backups, updates | Per-seat monthly |
| Enterprise | Larger orgs | Self-hosted at scale, SSO, compliance, support SLAs | Custom / annual license |

**Why this shape works:** the free layer costs you nothing to serve (it runs
on the user's own machine) and it's what spreads. The paid layer only kicks
in once there's an actual *team* problem — shared graph maintenance, sync,
uptime — which is a server problem the customer doesn't want to own
themselves. You're charging for aggregation and convenience, not for the
core idea.

**Pricing lean:** per-seat, not per-server. Per-server pricing punishes teams
for growing, which resents the tool right when it's providing the most
value. Per-seat scales with value delivered.

## 5. Go-To-Market

### Phase 1 — Build in public (pre-launch)
- Document the build process publicly (X/Twitter, a devlog, or a blog).
  Dev tool audiences respond well to watching the thing get built — it
  builds trust before there's even a product.
- Use your own past repos as the first "customer zero" — dogfood the tool
  building itself. This is a genuinely good story to tell publicly.

### Phase 2 — Open source core + launch
- Open source the local graph engine and the editor extension. This is what
  earns GitHub stars — people can try it in under a minute with no signup,
  which is the single biggest lever for organic spread in dev tooling.
- Keep the hosted team-sync layer, and any enterprise features, closed /
  paid. This is the standard "open core" model (see: Supabase, n8n, Sentry).
- Launch with a short (15–30 second) demo video showing one concrete "aha"
  moment: the tool surfacing forgotten context exactly when it's needed.
  This kind of visceral demo outperforms feature lists on Hacker News and
  Twitter by a wide margin.
- Launch venues: Hacker News (Show HN), r/programming, Product Hunt,
  relevant dev Twitter/X, and any AI-coding-agent communities (Claude Code,
  Cursor users).

### Phase 3 — Team expansion motion
- Individual users bring the tool into their team once they've felt the
  value solo. This is the natural free-to-paid conversion moment: "my
  personal graph is great, now the whole team needs to share one."
- Target teams already using AI coding agents heavily — they feel the
  context-starvation problem most acutely and are primed to pay for a fix.

## 6. Differentiation ("Why not just use Obsidian?")

Obsidian is a *manual* tool: you write notes, you draw the links yourself.
This product's core IP is the **automatic graph-building engine** — it
watches git history, commits, and code structure and infers the links
without the developer doing any manual linking. The note-taking UI on top is
the easy, almost commodity part; the auto-graph-construction and the
relevance-ranking logic (what to surface, when) is the actual moat.

Secondary differentiation: it's built *for* the AI-agent era specifically —
it exists to feed better context into Claude Code, Cursor, Copilot, etc., not
just to be a personal wiki.

## 7. Risks & Open Questions

- **Cold start on the graph:** a brand-new user has no history yet — first
  session needs to feel useful fast (e.g., immediately parsing existing git
  history rather than waiting for new activity).
- **Embedding quality for code:** generic text embeddings are noticeably
  worse than code-aware embeddings; this needs real evaluation work, not
  assumption.
- **Competitive attention:** context/memory-for-coding-agents is an active,
  fast-moving space right now — speed to a working open-source core matters
  more than a fully-polished v1.
- **Privacy trust:** developers will be (rightly) cautious about a tool that
  reads their entire codebase. Local-first architecture and clear "your code
  never leaves your machine unless you choose hosted" messaging is not
  optional — it's core to adoption.

## 8. Milestones (business side)

1. Working local MVP, used daily by you, on your own repos.
2. Open source release + public demo video + Show HN launch.
3. First 100 GitHub stars / first external users.
4. First team (even a team of 2–3) using the shared graph.
5. First paying team.
6. Enterprise conversation / pilot.
