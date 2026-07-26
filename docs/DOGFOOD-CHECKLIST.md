# Dogfood checklist — FR smoke (E1–E7)

Use after `./scripts/install.sh` + `./scripts/dev.sh`. Fixture: `fixtures/dogfood-rate-limits`.

## Privacy (FR-19 / FR-24)

- [ ] README states local-first / no upload by default
- [ ] Settings shows `allow_code_upload=false`, no cloud account required

## Epic 1 — Core

- [ ] `GET /health` → ok, version, bind `127.0.0.1`
- [ ] `~/.mycelium/config.toml` exists

## Epic 2 — Index Graph

- [ ] Register dogfood git workspace
- [ ] Index completes with commits + symbols + co-change edges
- [ ] Cancel does not leave Core dead
- [ ] File-changed hook / watcher updates symbols

## Epic 3 — Local RAG

- [ ] Embeddings status shows model (MiniLM or hashing)
- [ ] `POST /query` returns ≤10 typed results (not mock)
- [ ] `POST /context/focus` on `src/ratelimit.py` + `calculate_jitter`

## Epic 4 — Vault

- [ ] Create/update/delete `.md` under vault path
- [ ] `[[wikilinks]]` + backlinks
- [ ] Note appears in search
- [ ] Create bucket → `_index.md` scaffold; note created with `bucket`
- [ ] `GET /vault/tree` shows folders; `POST /vault/pack` stays under `max_tokens` (no embeddings)

## Epic 5 — Desktop

- [ ] Library / Index / Search / Vault / Settings usable
- [ ] Vault sidebar shows folder tree; new bucket + note-in-bucket
- [ ] Core offline banner + Retry
- [ ] Note result from Search opens Vault

## Epic 6 — Editor

- [ ] Status bar Connected/Offline
- [ ] Side Panel focus packet
- [ ] Mycelium: New Note creates linked vault note

## Epic 7 — MCP

- [ ] `mycelium_search` / `mycelium_focus` / `mycelium_get_note` / `mycelium_commits_for_path`
- [ ] `mycelium_vault_tree` / `mycelium_vault_pack` (no RAG)
- [ ] Note from Desktop visible via MCP without separate DB

## Epic 8 — Hardening

- [ ] `./scripts/install.sh` succeeds on clean machine path
- [ ] `./venv/bin/python scripts/eval_embeddings.py` writes `docs/EMBEDDING-EVAL.md`
- [ ] Demo script (`docs/DEMO.md`) completed once

## Epic 9 — Vault buckets dual-path

- [ ] Structure pack then optional RAG as in DEMO §2b / MCP tree→pack→get_note
