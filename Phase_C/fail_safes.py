"""Fail-safe checks that can veto a proposed trade."""
from __future__ import annotations

from dataclasses import dataclass

from Shared.config import Config
from Shared.models import PriceSnapshot


@dataclass(frozen=True)
class FailSafeReport:
    approved: bool
    checks: dict[str, bool]
    reasons: list[str]


class FailSafeEvaluator:
    """Evaluate drawdown, liquidity, and buying power constraints."""

    def evaluate(
        self,
        *,
        snapshot: PriceSnapshot,
        buying_power: float,
        daily_loss: float,
        weekly_loss: float,
    ) -> FailSafeReport:
        spread = max(snapshot.yes_ask - snapshot.yes_bid, snapshot.no_ask - snapshot.no_bid)

        checks = {
            "buying_power_floor": buying_power >= Config.MIN_BUYING_POWER,
            "daily_drawdown": daily_loss <= Config.DRAWDOWN_DAILY_LIMIT,
            "weekly_drawdown": weekly_loss <= Config.DRAWDOWN_WEEKLY_LIMIT,
            "liquidity_volume": snapshot.volume >= 1000,
            "liquidity_spread": spread <= 8,
        }
        approved = all(checks.values())
        reasons = [k for k, ok in checks.items() if not ok]
        return FailSafeReport(approved=approved, checks=checks, reasons=reasons)
