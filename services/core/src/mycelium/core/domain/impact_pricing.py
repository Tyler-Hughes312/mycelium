"""API list-price estimates for Impact $ savings (input tokens only)."""

from __future__ import annotations

from typing import Any

IMPACT_PRICING_DISCLAIMER = (
    "Estimated vs dumping matched files into the model context. "
    "Uses API list prices you can edit in Settings — not Cursor subscription billing. "
    "When Cursor does not send a model id, Mycelium uses your Impact default model "
    "and labels it Assumed."
)

DEFAULT_INPUT_RATES_USD_PER_1M: dict[str, float] = {
    "claude-sonnet-4": 3.0,
    "claude-opus-4": 15.0,
    "claude-haiku-3.5": 0.8,
    "gpt-4o": 2.5,
    "gpt-4.1": 2.0,
    "gemini-2.5-flash": 0.15,
    "gemini-2.5-pro": 1.25,
}

_PROBE_KEYS = (
    "model",
    "model_id",
    "modelId",
    "llm",
    "cursor/model",
    "anthropic/model",
    "openai/model",
)


def compute_usd_saved(*, tokens_saved: int, usd_per_1m_input: float) -> float:
    if tokens_saved <= 0 or usd_per_1m_input <= 0:
        return 0.0
    return float(tokens_saved) / 1_000_000.0 * float(usd_per_1m_input)


def effective_rates(overrides: dict[str, float] | None) -> dict[str, float]:
    rates = dict(DEFAULT_INPUT_RATES_USD_PER_1M)
    if overrides:
        for k, v in overrides.items():
            key = str(k).strip()
            if not key:
                continue
            try:
                rates[key] = float(v)
            except (TypeError, ValueError):
                continue
    return rates


def rate_for_model(model_id: str, overrides: dict[str, float] | None) -> float:
    mid = (model_id or "").strip()
    if not mid:
        return 0.0
    return float(effective_rates(overrides).get(mid, 0.0))


def _extract_model_from_probe(probe: dict[str, Any] | None) -> tuple[str, str]:
    if not probe:
        return "", ""
    for key in _PROBE_KEYS:
        if key in probe and probe[key]:
            return str(probe[key]).strip(), key
    meta = probe.get("_meta") if isinstance(probe.get("_meta"), dict) else None
    if meta:
        for key in _PROBE_KEYS:
            if key in meta and meta[key]:
                return str(meta[key]).strip(), f"_meta.{key}"
    return "", ""


def pricing_table(
    *,
    default_model: str,
    overrides: dict[str, float] | None,
) -> dict[str, Any]:
    effective = effective_rates(overrides)
    override_keys = set(overrides or {})
    rates: list[dict[str, Any]] = []
    for model_id, usd_per_1m_input in effective.items():
        shipped = DEFAULT_INPUT_RATES_USD_PER_1M.get(model_id)
        overridden = model_id in override_keys and (
            shipped is None or float(usd_per_1m_input) != float(shipped)
        )
        rates.append(
            {
                "id": model_id,
                "usd_per_1m_input": float(usd_per_1m_input),
                "overridden": overridden,
            }
        )
    return {
        "default_model": (default_model or "").strip(),
        "rates": rates,
        "disclaimer": IMPACT_PRICING_DISCLAIMER,
    }


def resolve_model(
    *,
    probe: dict[str, Any] | None,
    default_model: str,
) -> tuple[str, str, str]:
    inferred, probe_key = _extract_model_from_probe(probe)
    if inferred:
        return inferred, "inferred", probe_key[:120]
    default = (default_model or "").strip()
    if default:
        return default, "default", ""
    return "", "unknown", ""
