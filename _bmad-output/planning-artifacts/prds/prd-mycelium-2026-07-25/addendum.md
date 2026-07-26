# Mycelium PRD Addendum

Downstream technical depth that does not belong in the PRD capability narrative.

## Competitive landscape (2026 snapshot)

Local/agent memory space is crowded: PMB, Mimir, agentmemory (MCP memory), CodeMem (hosted), plus editor-native sticky memory. Mycelium’s wedge is the fusion of (1) auto Graph from git + Symbols, (2) human Thinking Vault, (3) editor Side Panel, (4) same store via MCP — not chat-memory alone.

## Mechanism options considered

| Concern | Options | Lean |
|---|---|---|
| Core language | Python / Rust / TypeScript | Python 3.12 — fastest path for tree-sitter, embeddings, FastAPI; venv already present |
| Vector store | LanceDB / sqlite-vec / Chroma | LanceDB — embedded, FTS-capable patterns common in code RAG |
| Graph metadata | SQLite / Neo4j / NetworkX-only | SQLite for durable Nodes/Edges; in-memory traversal OK for MVP scale |
| Embeddings | jina-v2-base-code / nomic-embed-text-v1.5 / nomic-embed-code 7B | jina-v2-base-code default (~307MB laptop); 7B deferred |
| Editor | VS Code API / JetBrains / CLI-only | VS Code/Cursor first |
| Agent surface | MCP / REST-only / hooks injection | MCP + localhost REST; hooks later |

## Rejected for MVP

- Hosted inference (cost + privacy conflict with local-first)
- Slack ingestion (dilutes core loop proof)
- Graph viz as primary UI (Obsidian proved it’s secondary)

## Personas (expanded)

Kept out of PRD spine; journeys carry enough. Alex/Jordan/Sam are archetypes of AI-heavy ICs, not separate market segments for v0.

## Sizing (soft)

Solo MVP: months not years; prove loop on dogfood + early external AI-heavy users before team sync investment.
