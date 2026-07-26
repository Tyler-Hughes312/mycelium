# Story 9.1: Vault buckets + dual-path context

Status: done

## Delivered

- Buckets = vault folders; `_index.md` scaffold via `POST /vault/buckets`
- Notes createable with `bucket`; ids `note:folder/stem`
- `GET /vault/tree` — structure map (no embeddings)
- `POST /vault/pack` — token-budget pack (map → indexes → bodies); `chars//4` estimate
- Note embeddings include `bucket:` (+ index role); nested notes still hybrid-RAG queryable
- MCP: `mycelium_vault_tree`, `mycelium_vault_pack`
- Desktop Vault: folder tree, new bucket, new note in selected bucket
