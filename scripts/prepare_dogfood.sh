#!/usr/bin/env bash
# Build / refresh the dogfood git fixture (Epic 8.2–8.3).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIX="$ROOT/fixtures/dogfood-rate-limits"

mkdir -p "$FIX/src"

cat > "$FIX/src/ratelimit.py" << 'PY'
"""Rate limiting helpers — planted for Mycelium dogfood / eval."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass


@dataclass
class TokenBucket:
    capacity: int
    refill_per_sec: float
    tokens: float = 0.0
    updated_at: float = 0.0

    def allow(self, cost: float = 1.0) -> bool:
        now = time.monotonic()
        if self.updated_at == 0.0:
            self.updated_at = now
            self.tokens = float(self.capacity)
        elapsed = now - self.updated_at
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
        self.updated_at = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False


def calculate_jitter(base_ms: int, attempt: int) -> int:
    """Jittered exponential backoff to avoid thundering herds after rate limits."""
    max_sleep = base_ms * (2 ** max(attempt, 0))
    max_sleep = min(max_sleep, 30_000)
    return random.randint(0, max_sleep)


def rate_limit_middleware(client_id: str, bucket: TokenBucket) -> bool:
    """Return True if the request may proceed."""
    return bucket.allow(1.0)
PY

cat > "$FIX/src/auth.py" << 'PY'
"""Auth helpers that depend on rate limiting."""

from __future__ import annotations


def authenticate(client_id: str, token: str) -> bool:
    """
    Authenticate a client. Applies rate_limit_middleware / TokenBucket and
    calculate_jitter backoff when limited (see src/ratelimit.py).
    """
    if not token:
        return False
    # Dogfood fixture: real wiring lives in ratelimit.py; this symbol is the
    # call-site agents should find when asking about auth + rate limits.
    _ = client_id
    return True
PY

cat > "$FIX/README.md" << 'MD'
# dogfood-rate-limits

Tiny fixture repo for Mycelium demo + embedding eval.
Planted topic: **rate limit retries / jittered backoff**.
MD

cat > "$FIX/queries.json" << 'JSON'
[
  {
    "id": "q1",
    "query": "how did we handle rate limits",
    "expect_any": ["rate_limit_middleware", "TokenBucket", "calculate_jitter", "rate limit"]
  },
  {
    "id": "q2",
    "query": "jittered backoff thundering herd",
    "expect_any": ["calculate_jitter", "jitter", "thundering"]
  },
  {
    "id": "q3",
    "query": "authenticate function rate limited",
    "expect_any": ["authenticate", "rate_limit_middleware"]
  },
  {
    "id": "q4",
    "query": "token bucket capacity refill",
    "expect_any": ["TokenBucket", "refill"]
  },
  {
    "id": "q5",
    "query": "commit about rate limit middleware",
    "expect_any": ["rate limit", "middleware", "jitter"]
  }
]
JSON

cd "$FIX"

# Fresh history each prepare so demo commits stay reproducible
rm -rf .git
git init -q
git config user.email "dogfood@mycelium.local"
git config user.name "Mycelium Dogfood"

git add README.md queries.json
git commit -qm "Initial dogfood fixture"

git add src/ratelimit.py
git commit -qm "Add token bucket rate limit middleware"

git add src/auth.py
git commit -qm "Wire authenticate to jittered rate-limit backoff"

echo "Dogfood fixture ready: $FIX"
git -C "$FIX" log --oneline | head -5
