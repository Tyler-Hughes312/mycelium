# Story 8.2: Embedding model eval harness

Status: done

## Delivered

- Fixture `fixtures/dogfood-rate-limits` + labeled `queries.json` (`scripts/prepare_dogfood.sh`)
- `scripts/eval_embeddings.py` — hashing vs MiniLM hit-rate → `docs/EMBEDDING-EVAL.md`
- Default remains `sentence-transformers/all-MiniLM-L6-v2` (winner on fixture; hashing for CI/offline)
