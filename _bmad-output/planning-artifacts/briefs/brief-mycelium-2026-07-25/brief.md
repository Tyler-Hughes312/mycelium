---
title: Mycelium
status: final
created: 2026-07-25
updated: 2026-07-25
---

# Product Brief: Mycelium

## One-liner

Mycelium is a local-first **codebase context layer** for AI-heavy developers: it indexes your repos (structure, symbols, git) and returns precise retrieval packets to editors and agents — so you burn fewer tokens re-reading and re-searching every session. An optional Thinking Vault holds decisions/ADRs; it is not a chat-memory product.

## Problem

AI coding agents are only as good as the context they get. Most sessions waste tokens re-pasting files or grepping the tree for code you already shipped. Session-memory tools (Memory Vault / Context Vault style) help agents remember *chat facts*; they do not primarily index the *codebase* for efficient, measurable retrieval. Hosted code RAG often wants your repo in the cloud.

## Who it’s for

AI-heavy solo and power developers using Cursor, Claude Code, Copilot, and similar tools — people who feel token burn and context starvation and will install a local tool without a sales call.

**Not for (v0):** enterprise procurement buyers, teams needing shared sync, people who want a hosted SaaS-only memory product.

## Solution (MVP)

1. **Local ingestion** — index repos from git history + tree-sitter structure into a graph.
2. **Local RAG** — laptop-sized embeddings + hybrid retrieval (vector + keyword), fully offline by default.
3. **Optional vault** — markdown notes with wikilinks/backlinks, linked to code entities (secondary).
4. **Surfacing** — VS Code/Cursor side panel shows ranked related commits, code, and notes for the current file/function.
5. **Agent bridge** — MCP (and local API) so agents query the same index without re-scanning the tree.

## Differentiation

| vs | Mycelium wedge |
|---|---|
| Agent memory / “context vault” | Codebase index + token-efficient packets; memory of chat is not the product |
| Obsidian | Auto-graph from code/git; notes are one layer, not the whole product |
| Hosted Code RAG | Local-first; code never leaves the machine by default |

## Business shape (post-MVP)

Open-core local product (adoption) → team/org shared graph (willingness to pay) → enterprise self-host. MVP proves the personal loop for external AI-heavy users first.

## Success for this brief

External AI-heavy developers install Mycelium, index a real repo, and within one session get a useful retrieval or note link they didn’t manually search for — and then wire it into their agent workflow.
