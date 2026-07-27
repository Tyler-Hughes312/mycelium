# Mycelium positioning

**One-liner:** Local-first **indexed retrieval** for your codebase — stop burning tokens re-reading and re-searching every AI session.

## What we are

- **Performance / efficiency product** for AI-heavy developers
- Indexes **repos** (symbols, files, commits) under `~/.mycelium`
- Returns a **precise context packet** to Cursor / Claude (MCP) and Desktop
- Headline metrics: **tokens saved**, **grounded %** (receipt-backed recalls), time not spent grepping / pasting files
- Agent loop: **session_start** → task tools → **cite receipt** (no second dump)

## What we are not

| Product shape | Optimized for | Mycelium? |
|---|---|---|
| Memory / Context Vault style tools | Remembering chat, decisions, notes across sessions | **No** — that’s a side layer at most |
| Generic “second brain” journal | Human PKM / agent diary | **No** as the primary pitch |
| Hosted code RAG SaaS | Cloud index of your repo | **No** — local-first by default |

Agent memory products treat **conversation history** as the asset. Mycelium treats **project structure and shipped code** as the asset. Token efficiency is the **headline**, not a side effect.

## Optional Thinking Vault

Markdown notes (buckets, wikilinks) can store ADRs and decisions linked to code. Useful — **secondary**. Do not lead marketing with “second brain” or “agent journal.”

## Numbers (honest)

| Claim | Status |
|---|---|
| **~60–90% fewer context tokens** | **Illustrative** on the marketing site — typical focus/search packet vs dumping whole matched files |
| **Live estimated $ saved** | Desktop **Impact** page + Core `impact` APIs — tokens saved vs a local baseline dump, converted with **editable API list-price rates** in Settings; **not** Cursor subscription billing |
| **Published customer benchmark / % time saved** | **Not yet** — dogfood Impact telemetry, then publish |

Until live dogfood numbers are published, always label site stats as illustrative and point people at Desktop Impact for their own machine.
