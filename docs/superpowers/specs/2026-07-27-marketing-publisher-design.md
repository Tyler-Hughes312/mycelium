# Mycelium Marketing Publisher — Design Spec

**Date:** 2026-07-27  
**Status:** Approved — implementing via `docs/superpowers/plans/2026-07-27-marketing-publisher.md`  
**Repo:** `Tyler-Hughes312/mycelium` (dogfood path `PlayingAround/MemoryOptimization`)  
**Related:** `docs/marketing/*`, vault `work/active/marketing-engine`, `reference/star-growth-playbook`

## Goal

Build agentic **publisher** infrastructure that markets Mycelium for Tyler — not a paste-queue.

**Success:** On a scheduled launch window, the system posts Show HN + Reddit for real (when credentials exist), logs outcomes to the Thinking Vault, and keeps Product Hunt / awesome-list PRs behind explicit approval.

## Decisions locked (from brainstorm)

| Decision | Choice |
|----------|--------|
| Autonomy | **Hybrid (C)** — launch-week autopilot for chosen channels; everything else approval-gated |
| Launch autopilot channels | **Hacker News (Show HN)** + **Reddit** only |
| Approach | **Reddit official API + Playwright for HN** |
| Accounts today | **Reddit ready**; **HN account not yet** (blocker for Show HN autopost) |
| Default subs | `r/LocalLLaMA`, `r/cursor`, `r/ClaudeAI` (staggered; author disclosed) |
| Out of scope for autopilot | X, Bluesky, LinkedIn, Product Hunt, awesome-list PRs |

## Non-goals

- Buying stars, fake upvotes, or engagement farms
- Inventing metrics / testimonials in posts
- Full social autopilot beyond HN + Reddit
- Storing secrets in git or vault plaintext beyond a local env file path reference
- Posting to HN before Tyler creates an HN account and completes one interactive login

## Architecture

```text
docs/marketing/drafts/*     ← source copy (versioned)
        │
        ▼
services/marketing/         ← publisher package (Python)
  publisher.py              ← CLI entry (dry-run | run | status | login-hn)
  channels/reddit.py        ← PRAW / Reddit API
  channels/hackernews.py    ← Playwright session
  schedule.py               ← launch-week timing + stagger
  guardrails.py             ← positioning + rate limits + dry-run gates
  state.json                ← local publish ledger (~/.mycelium/marketing/)
        │
        ├── secrets: ~/.mycelium/marketing.env
        ├── log → vault work/active/marketing-engine (via Core MCP or file append)
        └── scripts/marketing-publish.sh  ← thin wrapper
```

Cursor rule `mycelium-marketing.mdc` updates: marketing agent **runs the publisher** (dry-run first), does not stop at drafts.

## Hybrid publish modes

### Autopilot (launch week)

Triggers: `marketing-publish.sh run --wave launch` when:

1. `dry-run` previously passed for each channel
2. Credentials validate (`status` green)
3. Wall clock in configured window (default Tue/Wed **09:00 America/New_York**)
4. Ledger shows channel not already posted for this wave id

Order:

| Time (ET) | Action |
|-----------|--------|
| T+0 | Show HN (if HN session valid) — else skip + vault alert “HN blocked” |
| T+30m | Reddit `r/LocalLLaMA` |
| T+60m | Reddit `r/cursor` |
| T+90m | Reddit `r/ClaudeAI` |

Copy loaded from:

- `docs/marketing/drafts/show-hn.md` (title + body fenced blocks)
- `docs/marketing/drafts/reddit.md` (per-sub sections)

### Approval-gated

Queued items written to `~/.mycelium/marketing/queue.jsonl` and mirrored in vault marketing-engine:

- Product Hunt submission package
- Awesome-list PRs (`gh pr create` only after `approve <id>`)

CLI: `marketing-publish.sh queue list|approve <id>|reject <id>`

## Auth

### Reddit (ready path)

Env in `~/.mycelium/marketing.env`:

```bash
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USERNAME=
REDDIT_PASSWORD=          # or refresh-token flow if preferred later
REDDIT_USER_AGENT=mycelium-marketing/0.1 by u/<username>
```

Setup doc: `docs/marketing/SETUP-CREDENTIALS.md` — create “script” app at reddit.com/prefs/apps.

### Hacker News (blocked until account)

1. Tyler creates HN account manually
2. `marketing-publish.sh login-hn` opens Playwright Chromium → login once → persist storage state to `~/.mycelium/marketing/hn-storage.json`
3. Subsequent Show HN posts reuse storage state; on auth failure → fail closed, vault alert, no retry spam

No HN password stored in env if storage-state login works; optional `HN_USERNAME` for status display only.

## Guardrails

- **Positioning:** refuse to publish if draft body claims chat-memory vault product or unlabeled fake % savings
- **Idempotency:** wave id + channel + target → at most one successful post
- **Rate limits:** min 25 minutes between Reddit posts; max 3 Reddit posts / 24h from this tool
- **Disclosure:** Reddit bodies must include maker/author disclosure (template enforced)
- **Dry-run default:** `run` requires `--i-understand` or env `MARKETING_AUTOPILOT=1`
- **Fail closed:** missing creds / CAPTCHA / 403 → skip channel, log, continue others

## CLI surface

```bash
./scripts/marketing-publish.sh status
./scripts/marketing-publish.sh dry-run --wave launch
./scripts/marketing-publish.sh login-hn
./scripts/marketing-publish.sh run --wave launch --i-understand
./scripts/marketing-publish.sh queue list
./scripts/marketing-publish.sh queue approve <id>
```

Exit codes: `0` ok, `2` partial (some channels skipped), `3` blocked (no channels ready).

## Observability

- Append-only ledger: `~/.mycelium/marketing/ledger.jsonl` (url, channel, timestamp, wave)
- Update Thinking Vault note `work/active/marketing-engine` Log table after each wave
- Optional: print star count via `gh api` before/after (informational only)

## Implementation sketch (not the plan)

1. Package under `services/marketing/` with pyproject extras or reuse Core venv + deps `praw`, `playwright`
2. Parser for draft markdown fences
3. Reddit + HN channel adapters
4. Shell wrapper + credentials setup doc
5. Update `docs/marketing/AGENT.md` + Cursor rule to invoke publisher
6. Tests: dry-run parse + guardrails unit tests (no live network in CI)

## Risks

| Risk | Mitigation |
|------|------------|
| HN CAPTCHA / ban risk for automation | Interactive login; low frequency; one Show HN per wave; human creates account with normal history first |
| Reddit spam filters / ban | Stagger, disclose author, tailor copy, respect sub rules |
| Credential leak | Local env only; gitignore; never commit `marketing.env` / `hn-storage.json` |
| Agent posts wrong product pitch | Guardrails scan + draft review in dry-run |

## Open items (pre-first live wave)

1. Tyler creates HN account and runs `login-hn`
2. Tyler creates Reddit script app and fills `marketing.env`
3. Choose first wave datetime (next Tue/Wed 9am ET recommended)
4. Confirm sub list still LocalLLaMA / cursor / ClaudeAI

## Approval

- Chat design: **approved** 2026-07-27 (Hybrid + Approach 1 + HN/Reddit)
- This file: **approved** (apply 2026-07-27) → plan + implement
