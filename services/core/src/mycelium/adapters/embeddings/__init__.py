"""Embeddings adapter package."""

from mycelium.adapters.embeddings.bootstrap import (
    DEFAULT_EMBEDDING_MODEL,
    bootstrap_embedder,
    status_dict,
)
from mycelium.adapters.embeddings.hashing import HashingEmbedder

__all__ = [
    "DEFAULT_EMBEDDING_MODEL",
    "HashingEmbedder",
    "bootstrap_embedder",
    "status_dict",
]
