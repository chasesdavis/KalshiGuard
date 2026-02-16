"""Fractional Kelly sizing for KalshiGuard risk-managed entries."""
from __future__ import annotations

from dataclasses import dataclass

from Shared.config import Config


@dataclass(frozen=True)
class KellyResult:
    kelly_fraction: float
    recommended_stake: float


class KellySizer:
    """Compute conservative position size with hard-dollar cap constraints."""

    def size_position(self, bankroll: float, probability_yes: float, entry_price_cents: float) -> KellyResult:
        b = max((100 - entry_price_cents) / entry_price_cents, 0.01)
        q = 1 - probability_yes
        raw_fraction = ((b * probability_yes) - q) / b
        fraction = max(0.0, raw_fraction) * Config.KELLY_FRACTION
        stake = min(bankroll * fraction, Config.MAX_TRADE_RISK)
        return KellyResult(kelly_fraction=round(fraction, 6), recommended_stake=round(max(0.0, stake), 4))
