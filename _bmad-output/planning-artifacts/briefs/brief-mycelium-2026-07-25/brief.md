---
title: Mycelium
status: final
created: 2026-07-25
updated: 2026-07-25
---

# Product Brief: Mycelium

## One-liner

Mycelium is a local-first second brain for AI-heavy developers: it auto-grows a knowledge graph from your code and git history, pairs it with an Obsidian-style thinking vault, and surfaces the right context in your editor and agents via local RAG.

## Problem

AI coding agents are only as good as the context they get. Most sessions start near-zero: past decisions, abandoned approaches, and “why this weird function exists” live in git history, closed PRs, and one person’s head. Obsidian solves personal knowledge management but demands manual linking — discipline that dies on a fast-moving codebase. Session-memory tools for agents (PMB, Mimir, agentmemory, CodeMem) help agents remember *chat facts*; they do not primarily auto-build a *code+thinking* graph that also serves the human.

## Who it’s for

AI-heavy solo and power developers using Cursor, Claude Code, Copilot, and similar tools — people who already feel context starvation and will install a local tool without a sales call.

**Not for (v0):** enterprise procurement buyers, teams needing shared sync, people who want a hosted SaaS-only memory product.

## Solution (MVP)

1. **Local ingestion** — index repos from git history + tree-sitter structure into a graph.
2. **Local RAG** — laptop-sized embeddings + hybrid retrieval (vector + keyword), fully offline by default.
3. **Second brain vault** — markdown notes with wikilinks/backlinks, linked to code entities.
4. **Surfacing** — VS Code/Cursor side panel shows ranked related commits, code, and notes for the current file/function.
5. **Agent bridge** — MCP (and local API) so agents can query the same graph without reinventing memory.

## Differentiation

| vs | Mycelium wedge |
|---|---|
| Obsidian | Auto-graph from code/git; notes are one layer, not the whole product |
| Pure agent memory (PMB/Mimir/etc.) | Code-structure + git-aware graph + human thinking vault + editor UX, not only MCP memory |
| Hosted Code RAG (CodeMem etc.) | Local-first, open-core path; code never leaves the machine by default |

## Business shape (post-MVP)

Open-core local product (adoption) → team/org shared graph (willingness to pay) → enterprise self-host. MVP proves the personal loop for external AI-heavy users first.

## Success for this brief

External AI-heavy developers install Mycelium, index a real repo, and within one session get a useful retrieval or note link they didn’t manually search for — and then wire it into their agent workflow.
