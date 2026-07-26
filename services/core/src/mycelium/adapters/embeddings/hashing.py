"""Local hashing embedder — fully offline, no API key (FR-8 / AD-2).

Default MVP runtime. Optional SentenceTransformer models can replace this
via config once downloaded/cached under ~/.mycelium/models.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]+|[0-9]+")


class HashingEmbedder:
    """Deterministic bag-of-tokens hashing trick embedder."""

    model_id = "mycelium-hashing-v1"

    def __init__(self, dimension: int = 384) -> None:
        if dimension < 32:
            raise ValueError("dimension must be >= 32")
        self._dim = dimension

    def dimension(self) -> int:
        return self._dim

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        tokens = _TOKEN_RE.findall(text.lower())
        if not tokens:
            tokens = ["_empty"]
        for tok in tokens:
            digest = hashlib.sha256(tok.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "little") % self._dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign
        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]
