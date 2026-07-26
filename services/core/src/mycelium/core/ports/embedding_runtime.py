"""Embedding runtime port — local model adapter implements this later."""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable


@runtime_checkable
class EmbeddingRuntime(Protocol):
    """Local embedding inference (AD-2 / AD-4)."""

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""
        ...

    def dimension(self) -> int:
        """Embedding vector size for the active model."""
        ...
