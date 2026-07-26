# Embedding eval results

Generated: 2026-07-26 01:16 UTC
Fixture: `fixtures/dogfood-rate-limits`

## Summary

| Model | Backend | Hits | Hit rate |
|---|---|---:|---:|
| `mycelium-hashing-v1` | hashing | 5/5 | 100% |
| `sentence-transformers/all-MiniLM-L6-v2` | sentence-transformers | 5/5 | 100% |

**Winner (this run):** `sentence-transformers/all-MiniLM-L6-v2` (100% hit rate).

## Default in config

Ship default remains `sentence-transformers/all-MiniLM-L6-v2` (semantic quality vs hashing). Hashing stays available for offline tests / CI.

To try Jina code embeddings later:

```toml
# ~/.mycelium/config.toml
[embedding]
model = "jinaai/jina-embeddings-v2-base-code"
```

## Per-query detail

### mycelium-hashing-v1

- [PASS] `q1` how did we handle rate limits → File:queries.json, File:README.md, File:src/ratelimit.py
- [PASS] `q2` jittered backoff thundering herd → File:queries.json, Function:calculate_jitter, File:README.md
- [PASS] `q3` authenticate function rate limited → Function:authenticate, Function:calculate_jitter, Function:rate_limit_middleware
- [PASS] `q4` token bucket capacity refill → File:queries.json, Commit:Add token bucket rate limit middleware, File:src/ratelimit.py
- [PASS] `q5` commit about rate limit middleware → Commit:Add token bucket rate limit middleware, Commit:Wire authenticate to jittered rate-limit backoff, Commit:Initial dogfood fixture

### sentence-transformers/all-MiniLM-L6-v2

- [PASS] `q1` how did we handle rate limits → File:src/auth.py, Function:authenticate, File:src/ratelimit.py
- [PASS] `q2` jittered backoff thundering herd → Function:calculate_jitter, File:src/ratelimit.py, File:queries.json
- [PASS] `q3` authenticate function rate limited → Function:authenticate, Function:rate_limit_middleware, Function:calculate_jitter
- [PASS] `q4` token bucket capacity refill → Class:TokenBucket, File:queries.json, File:src/ratelimit.py
- [PASS] `q5` commit about rate limit middleware → Commit:Add token bucket rate limit middleware, Commit:Wire authenticate to jittered rate-limit backoff, Commit:Initial dogfood fixture

