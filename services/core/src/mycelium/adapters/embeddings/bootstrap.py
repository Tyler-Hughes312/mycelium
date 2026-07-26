"""Embedding bootstrap — resolve runtime, cache dir, optional ST model (FR-8)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mycelium.adapters.embeddings.hashing import HashingEmbedder
from mycelium.core.ports.embedding_runtime import EmbeddingRuntime

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingStatus:
    model_id: str
    offline: bool
    cache_dir: str
    dimension: int
    backend: str
    notice: str


def default_models_dir(home: Path | None = None) -> Path:
    root = home or (Path.home() / ".mycelium")
    path = root / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def bootstrap_embedder(
    *,
    model: str = "mycelium-hashing-v1",
    cache_dir: Path | None = None,
    dimension: int = 384,
) -> tuple[EmbeddingRuntime, EmbeddingStatus]:
    """
    Create an EmbeddingRuntime.

    - `mycelium-hashing-v1` (default): immediate offline, no download
    - any other id: attempt sentence-transformers load from cache_dir;
      on failure, fall back to hashing with a clear notice
    """
    cache = cache_dir or default_models_dir()
    cache.mkdir(parents=True, exist_ok=True)

    if model in {"mycelium-hashing-v1", "hashing", "local-hash"}:
        runtime: EmbeddingRuntime = HashingEmbedder(dimension=dimension)
        status = EmbeddingStatus(
            model_id=HashingEmbedder.model_id,
            offline=True,
            cache_dir=str(cache),
            dimension=runtime.dimension(),
            backend="hashing",
            notice="Using offline hashing embedder (no download required).",
        )
        logger.info(status.notice)
        return runtime, status

    # Optional heavy path
    try:
        from mycelium.adapters.embeddings.sentence_transformers_runtime import (
            SentenceTransformerEmbedder,
        )

        runtime = SentenceTransformerEmbedder(model_name=model, cache_dir=cache)
        status = EmbeddingStatus(
            model_id=model,
            offline=True,
            cache_dir=str(cache),
            dimension=runtime.dimension(),
            backend="sentence-transformers",
            notice=f"Loaded embedding model '{model}' from cache {cache}.",
        )
        logger.info(status.notice)
        return runtime, status
    except Exception as exc:  # noqa: BLE001
        runtime = HashingEmbedder(dimension=dimension)
        status = EmbeddingStatus(
            model_id=HashingEmbedder.model_id,
            offline=True,
            cache_dir=str(cache),
            dimension=runtime.dimension(),
            backend="hashing",
            notice=(
                f"Model '{model}' unavailable ({exc}); "
                f"falling back to offline hashing embedder."
            ),
        )
        logger.warning(status.notice)
        return runtime, status


def status_dict(status: EmbeddingStatus) -> dict[str, Any]:
    return {
        "model_id": status.model_id,
        "offline": status.offline,
        "cache_dir": status.cache_dir,
        "dimension": status.dimension,
        "backend": status.backend,
        "notice": status.notice,
    }
