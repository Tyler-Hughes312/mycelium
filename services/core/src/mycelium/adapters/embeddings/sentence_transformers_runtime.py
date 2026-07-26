"""Optional SentenceTransformer embedding runtime."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path


class SentenceTransformerEmbedder:
    def __init__(self, *, model_name: str, cache_dir: Path) -> None:
        from sentence_transformers import SentenceTransformer

        cache_dir.mkdir(parents=True, exist_ok=True)
        self._model_name = model_name
        self._model = SentenceTransformer(
            model_name,
            cache_folder=str(cache_dir),
        )
        # Probe dimension
        probe = self._model.encode(["dimension probe"], normalize_embeddings=True)
        self._dim = int(len(probe[0]))

    def dimension(self) -> int:
        return self._dim

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = self._model.encode(
            list(texts),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [list(map(float, row)) for row in vectors]
