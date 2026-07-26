# Story 3.3: Hybrid RAG Query API

Status: done

## Story

As an AI-heavy developer,
I want natural-language search over my Graph,
So that I can ask “how did we do X?” (FR-9).

## Acceptance Criteria

1. `POST /query` returns Context Packet ≤10 results — **done**
2. Results fuse vector + FTS via RRF with typed provenance — **done** (AD-4)

## Delivered

- `RagService.query` (vector + FTS + RRF)
- Real `POST /query` `{ query, workspace_id, limit }` (mock removed)
- Desktop Search wired to real query + workspace picker
