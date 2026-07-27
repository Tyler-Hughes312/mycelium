# Marketing Publisher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a local CLI publisher that can dry-run and (with credentials) autopost Show HN + Reddit launch waves, with approval-gated queue for everything else.

**Architecture:** Standalone Python package under `services/marketing/` (stdlib + praw + playwright). Drafts parsed from `docs/marketing/drafts/`. Secrets and ledger under `~/.mycelium/marketing/`. Thin shell wrapper `scripts/marketing-publish.sh`.

**Tech Stack:** Python 3.12+, praw, playwright, pytest

**Spec:** `docs/superpowers/specs/2026-07-27-marketing-publisher-design.md`

## Global Constraints

- Never commit `~/.mycelium/marketing.env` or `hn-storage.json`
- Positioning: refuse chat-memory-vault pitch / unlabeled fake % savings
- `run` requires `--i-understand` or `MARKETING_AUTOPILOT=1`
- Min 25 min between Reddit posts; max 3 Reddit / 24h from this tool
- Fail closed per channel; continue others
- Skip git commits unless Tyler explicitly asks
- No live network calls in CI tests

## File map

| File | Responsibility |
|------|----------------|
| `services/marketing/pyproject.toml` | Package metadata + deps |
| `services/marketing/src/mycelium_marketing/__init__.py` | Version |
| `services/marketing/src/mycelium_marketing/paths.py` | Repo root + `~/.mycelium/marketing` |
| `services/marketing/src/mycelium_marketing/drafts.py` | Parse show-hn / reddit markdown |
| `services/marketing/src/mycelium_marketing/guardrails.py` | Content + rate + disclosure checks |
| `services/marketing/src/mycelium_marketing/ledger.py` | Idempotent ledger + queue |
| `services/marketing/src/mycelium_marketing/schedule.py` | Launch wave job list + stagger |
| `services/marketing/src/mycelium_marketing/channels/reddit.py` | PRAW submit |
| `services/marketing/src/mycelium_marketing/channels/hackernews.py` | Playwright submit + login |
| `services/marketing/src/mycelium_marketing/vault_log.py` | Append marketing-engine log line |
| `services/marketing/src/mycelium_marketing/publisher.py` | CLI |
| `services/marketing/tests/test_drafts.py` | Draft parse tests |
| `services/marketing/tests/test_guardrails.py` | Guardrail tests |
| `services/marketing/tests/test_schedule.py` | Wave job tests |
| `scripts/marketing-publish.sh` | Wrapper |
| `docs/marketing/SETUP-CREDENTIALS.md` | Auth setup |
| `docs/marketing/AGENT.md` | Invoke publisher |
| `docs/marketing/drafts/reddit.md` | Ensure author disclosure |
| `.gitignore` | Ignore marketing secrets if nested |
| `templates/cursor/mycelium-marketing.mdc` | Run publisher |

---

### Task 1: Draft parser + guardrails + schedule (TDD)

**Files:**
- Create: all `services/marketing/**` modules listed above except live channel network bodies can stub
- Test: `services/marketing/tests/test_*.py`

**Interfaces:**
- Produces: `parse_show_hn(path) -> ShowHNDraft(title, body)`, `parse_reddit(path) -> list[RedditDraft(subreddit, title, body)]`, `check_content(text) -> list[str]`, `launch_jobs(wave_id) -> list[Job]`

- [ ] **Step 1: Scaffold package + failing tests**
- [ ] **Step 2: Implement drafts, guardrails, schedule, ledger until tests pass**
- [ ] **Step 3: Run** `cd services/marketing && python -m pytest -q`

### Task 2: Reddit + HN channel adapters + CLI

**Files:**
- Create: `channels/reddit.py`, `channels/hackernews.py`, `publisher.py`, `vault_log.py`
- Create: `scripts/marketing-publish.sh`

**Interfaces:**
- Produces: CLI commands `status|dry-run|run|login-hn|queue`

- [ ] **Step 1: Implement adapters (network behind clear functions)**
- [ ] **Step 2: Wire CLI + shell wrapper**
- [ ] **Step 3: `dry-run --wave launch` works without credentials**

### Task 3: Docs + agent wiring + draft disclosure

**Files:**
- Create: `docs/marketing/SETUP-CREDENTIALS.md`
- Modify: `docs/marketing/AGENT.md`, `README.md` (marketing), drafts, cursor rule, spec status

- [ ] **Step 1: Credentials doc + agent runbook update**
- [ ] **Step 2: Ensure reddit drafts include author disclosure**
- [ ] **Step 3: Update vault marketing-engine via MCP**
- [ ] **Step 4: Verify pytest + dry-run**

---

## Spec coverage check

| Spec item | Task |
|-----------|------|
| Reddit API + Playwright HN | 2 |
| Hybrid queue approve | 2 |
| Guardrails / dry-run / ledger | 1–2 |
| SETUP-CREDENTIALS + AGENT | 3 |
| Exit codes 0/2/3 | 2 |
