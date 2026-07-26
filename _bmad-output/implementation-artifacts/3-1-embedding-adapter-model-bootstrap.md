# Story 3.1: Embedding adapter + model bootstrap

Status: done

## Story

As a developer,
I want local Embeddings without an API key,
So that RAG works offline after model download (FR-8).

## Acceptance Criteria

1. First embedding request uses a clear offline bootstrap path — **done**
2. Subsequent embeds run fully offline — **done** (`mycelium-hashing-v1` default; optional ST model via config)

## Delivered

- `HashingEmbedder` + `bootstrap_embedder` under `adapters/embeddings/`
- Optional `SentenceTransformerEmbedder` when configured model is available
- `GET /embeddings/status` + embedding block on `/health`
- Config `[embedding] model` (default hashing; can point at jina / HF ids)
