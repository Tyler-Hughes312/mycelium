"""Local impact / token-savings estimates for recall paths."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mycelium.adapters.store.impact_store import ImpactStore
from mycelium.core.domain.impact_pricing import (
    compute_usd_saved,
    rate_for_model,
    resolve_model,
)
from mycelium.core.domain.vault_service import estimate_tokens

_MAX_FILE_CHARS = 200_000


def compute_tokens_saved(*, served: int, baseline: int) -> int:
    return max(0, int(baseline) - int(served))


def estimate_pack_impact(*, tokens_est: int, max_tokens: int) -> tuple[int, int, int]:
    served = max(0, int(tokens_est))
    baseline = max(int(max_tokens), served)
    return served, baseline, compute_tokens_saved(served=served, baseline=baseline)


def estimate_query_impact(
    *,
    snippets: list[str],
    path_texts: dict[str, str],
) -> tuple[int, int, int]:
    served = estimate_tokens("\n".join(snippets)) if snippets else 0
    if path_texts:
        baseline = estimate_tokens(
            "\n".join(t[:_MAX_FILE_CHARS] for t in path_texts.values())
        )
        baseline = max(baseline, served)
    else:
        baseline = max(served * 4, served)
    return served, baseline, compute_tokens_saved(served=served, baseline=baseline)


class ImpactService:
    def __init__(
        self,
        store: ImpactStore,
        *,
        enabled: bool = True,
        default_model: str = "claude-sonnet-4",
        pricing_overrides: dict[str, float] | None = None,
    ) -> None:
        self.store = store
        self.enabled = enabled
        self.default_model = default_model
        self.pricing_overrides = pricing_overrides

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def set_pricing(
        self,
        *,
        default_model: str,
        pricing_overrides: dict[str, float] | None,
    ) -> None:
        self.default_model = default_model
        self.pricing_overrides = pricing_overrides

    def _record(
        self,
        *,
        tool: str,
        workspace_id: str | None,
        served: int,
        baseline: int,
        saved: int,
        probe: dict | None = None,
        receipt_id: str | None = None,
    ) -> None:
        if not self.enabled:
            return
        model_id, model_source, model_probe = resolve_model(
            probe=probe,
            default_model=self.default_model,
        )
        usd_per_1m_input = rate_for_model(model_id, self.pricing_overrides)
        usd_saved = compute_usd_saved(
            tokens_saved=saved,
            usd_per_1m_input=usd_per_1m_input,
        )
        event: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tool": tool,
            "workspace_id": workspace_id or "",
            "served_tokens": served,
            "baseline_tokens": baseline,
            "tokens_saved": saved,
            "model_id": model_id,
            "model_source": model_source,
            "model_probe": model_probe,
            "usd_per_1m_input": usd_per_1m_input,
            "usd_saved": usd_saved,
            "grounded": bool(receipt_id),
        }
        if receipt_id:
            event["receipt_id"] = receipt_id
        self.store.append(event)

    def record_pack(
        self,
        *,
        pack: dict[str, Any],
        max_tokens: int,
        workspace_id: str | None = None,
        probe: dict | None = None,
        receipt_id: str | None = None,
    ) -> None:
        served, baseline, saved = estimate_pack_impact(
            tokens_est=int(pack.get("tokens_est") or 0),
            max_tokens=max_tokens,
        )
        self._record(
            tool="vault_pack",
            workspace_id=workspace_id,
            served=served,
            baseline=baseline,
            saved=saved,
            probe=probe,
            receipt_id=receipt_id,
        )

    def record_search_or_focus(
        self,
        *,
        tool: str,
        payload: dict[str, Any],
        workspace_root: Path | None = None,
        probe: dict | None = None,
        receipt_id: str | None = None,
    ) -> tuple[int, int, int]:
        results = payload.get("results") or []
        snippets: list[str] = []
        path_texts: dict[str, str] = {}
        for row in results:
            if not isinstance(row, dict):
                continue
            snip = str(row.get("snippet") or row.get("text") or "")
            if snip:
                snippets.append(snip)
            path = str(row.get("path") or row.get("file_path") or "")
            if path and workspace_root is not None and path not in path_texts:
                fp = Path(path)
                if not fp.is_absolute():
                    fp = workspace_root / path
                try:
                    if fp.is_file():
                        path_texts[path] = fp.read_text(
                            encoding="utf-8", errors="ignore"
                        )[:_MAX_FILE_CHARS]
                except OSError:
                    pass
        served, baseline, saved = estimate_query_impact(
            snippets=snippets, path_texts=path_texts
        )
        self._record(
            tool=tool,
            workspace_id=str(payload.get("workspace_id") or ""),
            served=served,
            baseline=baseline,
            saved=saved,
            probe=probe,
            receipt_id=receipt_id,
        )
        return served, baseline, saved