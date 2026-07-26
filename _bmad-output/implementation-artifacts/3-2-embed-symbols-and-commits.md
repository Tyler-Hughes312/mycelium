# Story 3.2: Embed Symbols and Commits

Status: done

## Story

As a developer,
I want indexed content embedded into the vector store,
So that semantic search works.

## Acceptance Criteria

1. Vectors exist keyed by Node ID after embed pass — **done** (`vectors.json`)
2. Re-embed on content hash change only — **done**

## Delivered

- `JsonVectorStore` content-hash upsert
- `EmbeddingService.embed_workspace` / `embed_symbols`
- Index phase `embeddings` after co-change; incremental hook re-embeds file symbols
- `POST /workspaces/{id}/embeddings`
