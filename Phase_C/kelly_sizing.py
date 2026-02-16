"""Fractional Kelly micro-sizing for Kalshi binary contracts."""
from __future__ import annotations

from dataclasses import dataclass

from Shared.config import Config


@dataclass(frozen=True)
class PositionSizeDecision:
    side: str
    recommended_risk: float
    kelly_fraction_raw: float
    kelly_fraction_applied: float
    max_risk_cap: float
    exposure_cap_remaining: float
    rationale: list[str]


class FractionalKellySizer:
    """Computes conservative position risk in dollars for a single trade."""

    def size_risk(
        self,
        *,
        side: str,
        prob_yes: float,
        bankroll: float,
        kelly_multiplier: float,
        exposure_cap_remaining: float,
    ) -> PositionSizeDecision:
        """Return risk budget in dollars, bounded by strict hard caps."""

        if side not in {"YES", "NO"}:
            return PositionSizeDecision(side, 0.0, 0.0, 0.0, Config.MAX_TRADE_RISK, exposure_cap_remaining, ["hold_side"])

        p_win = prob_yes if side == "YES" else (1 - prob_yes)
        p_win = min(max(p_win, 0.0), 1.0)

        # Binary contract approximation with conservative fixed b=1.
        q = 1 - p_win
        kelly_raw = max((p_win - q), 0.0)
        kelly_applied = kelly_raw * kelly_multiplier

        uncapped_risk = bankroll * kelly_applied
        cap = min(Config.MAX_TRADE_RISK, exposure_cap_remaining)
        recommended = round(max(min(uncapped_risk, cap), 0.0), 4)

        rationale = [
            f"kelly_multiplier={kelly_multiplier:.2f}x",
            f"p_win={p_win:.4f}",
            f"kelly_raw={kelly_raw:.4f}",
            f"uncapped_risk=${uncapped_risk:.4f}",
            f"hard_cap=${cap:.2f}",
        ]

        return PositionSizeDecision(
            side=side,
            recommended_risk=recommended,
            kelly_fraction_raw=round(kelly_raw, 6),
            kelly_fraction_applied=round(kelly_applied, 6),
            max_risk_cap=Config.MAX_TRADE_RISK,
            exposure_cap_remaining=exposure_cap_remaining,
            rationale=rationale,
        )
