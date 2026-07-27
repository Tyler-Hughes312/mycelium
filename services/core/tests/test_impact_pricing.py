from __future__ import annotations

from mycelium.core.domain.impact_pricing import (
    DEFAULT_INPUT_RATES_USD_PER_1M,
    compute_usd_saved,
    effective_rates,
    rate_for_model,
    resolve_model,
)


def test_compute_usd_saved() -> None:
    assert abs(compute_usd_saved(tokens_saved=100_000, usd_per_1m_input=3.0) - 0.3) < 1e-9
    assert compute_usd_saved(tokens_saved=0, usd_per_1m_input=3.0) == 0.0
    assert compute_usd_saved(tokens_saved=1000, usd_per_1m_input=0.0) == 0.0


def test_overrides_beat_defaults() -> None:
    rates = effective_rates({"claude-sonnet-4": 9.99})
    assert rates["claude-sonnet-4"] == 9.99
    assert "gpt-4o" in rates
    assert rate_for_model("missing-model", None) == 0.0


def test_resolve_model_inferred_from_probe() -> None:
    mid, src, probe = resolve_model(
        probe={"model": "claude-sonnet-4"},
        default_model="gpt-4o",
    )
    assert mid == "claude-sonnet-4"
    assert src == "inferred"
    assert "model" in probe


def test_resolve_model_falls_back_to_default() -> None:
    mid, src, _ = resolve_model(probe=None, default_model="gpt-4o")
    assert mid == "gpt-4o"
    assert src == "default"


def test_resolve_model_unknown_when_empty() -> None:
    mid, src, _ = resolve_model(probe={}, default_model="")
    assert mid == ""
    assert src == "unknown"


def test_shipped_table_has_core_models() -> None:
    for key in ("claude-sonnet-4", "gpt-4o", "gemini-2.5-flash"):
        assert key in DEFAULT_INPUT_RATES_USD_PER_1M
        assert DEFAULT_INPUT_RATES_USD_PER_1M[key] > 0
