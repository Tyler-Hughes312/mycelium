"""LLM provider port — opt-in generative completions (AD-2)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LlmProvider(Protocol):
    """Remote or local chat completion provider."""

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
    ) -> str:
        """Return assistant text for an OpenAI-style messages list."""
        ...
