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
        """Return fractional Kelly sizing clipped to strict risk caps.

        If inputs are invalid (non-positive bankroll or out-of-range entry), stake is zero.
        """
        if bankroll <= 0 or entry_price_cents <= 0 or entry_price_cents >= 100:
            return KellyResult(kelly_fraction=0.0, recommended_stake=0.0)

        prob_yes = min(max(probability_yes, 0.0), 1.0)
        b = (100 - entry_price_cents) / entry_price_cents
        q = 1 - prob_yes
        raw_fraction = ((b * prob_yes) - q) / b

        fraction = max(0.0, raw_fraction) * Config.KELLY_FRACTION
        stake = min(bankroll * fraction, Config.MAX_TRADE_RISK)
        return KellyResult(kelly_fraction=round(fraction, 6), recommended_stake=round(max(0.0, stake), 4))
