"""Optional SentenceTransformer embedding runtime."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

logger = logging.getLogger(__name__)


class SentenceTransformerEmbedder:
    def __init__(self, *, model_name: str, cache_dir: Path) -> None:
        from sentence_transformers import SentenceTransformer

        cache_dir.mkdir(parents=True, exist_ok=True)
        self._model_name = model_name
        logger.info(
            "Loading embedding model '%s' (download once into %s if missing)…",
            model_name,
            cache_dir,
        )
        # cache_folder keeps HF/ST weights under ~/.mycelium/models
        self._model = SentenceTransformer(
            model_name,
            cache_folder=str(cache_dir),
        )
        probe = self._model.encode(["dimension probe"], normalize_embeddings=True)
        self._dim = int(len(probe[0]))
        logger.info(
            "Embedding model ready: %s (dim=%s)",
            model_name,
            self._dim,
        )

    def dimension(self) -> int:
        return self._dim

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=32,
        )
        return [list(map(float, row)) for row in vectors]
