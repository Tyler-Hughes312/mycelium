# Context receipts (proof-carrying agent turns)

**Date:** 2026-07-27  
**Constraint:** Receipts must **not** dump more context — they attest which relevant hits were already served.

## Problem

Agents re-grep and re-dump files even after Mycelium returned a tight packet.

## Design

1. Every Search / Focus / Vault pack mints a **compact receipt** (`rcp_…`): tool, workspace, git head, item ids/paths/titles, `served_tokens`. **No snippets or bodies.**
2. MCP packets append **one line**: `receipt=… head=… items=N served~T (cite receipt; do not re-fetch…)`
3. `GET /context/receipts/{id}` + `mycelium_verify_receipt` return status + path list only.
4. Impact events store `receipt_id` / `grounded`; summary exposes `grounded_pct`.
5. Session/task tools use **lower token budgets** (brain ≤600/400, vault slices ≤350) so bootstrap stays relevant-only.

## Non-goals

- Enforcing receipts inside Cursor (policy + Impact scoreboard only)
- Storing packet bodies inside the receipt store
