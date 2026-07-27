"""Echo LLM — deterministic test/dev provider (no network)."""

from __future__ import annotations


class EchoLlm:
    """Returns a truncated echo of the last user message."""

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
    ) -> str:
        _ = model
        last = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        return f"echo: {last[:500]}"
