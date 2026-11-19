"""Estimated cost from a user-maintained price table (`pricing.yaml`)."""

from pathlib import Path

import yaml


def load_prices(path: Path) -> dict[str, dict[str, float]]:
    """Read `{"provider:model": {"input_per_1m": x, "output_per_1m": y}}`; a missing file means no prices."""
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {k: v for k, v in data.items() if v and v.get("input_per_1m") is not None}


def estimate_cost(
    prices: dict[str, dict[str, float]], model_id: str, input_tokens: int | None, output_tokens: int | None
) -> float | None:
    """Cost in USD, or None when the price or the token counts are unknown."""
    price = prices.get(model_id)
    if price is None or input_tokens is None or output_tokens is None:
        return None
    return (input_tokens * price["input_per_1m"] + output_tokens * price["output_per_1m"]) / 1_000_000
