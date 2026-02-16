"""Fail-safe checks to preserve the $50 bankroll during paper/live gating."""
from __future__ import annotations

from dataclasses import dataclass

from Shared.config import Config
from Shared.bankroll_tracker import BankrollTracker


@dataclass(frozen=True)
class FailSafeResult:
    allowed: bool
    reasons: list[str]


class FailSafeGate:
    """Enforce pre-trade hard caps and drawdown kill switches."""

    def evaluate(self, tracker: BankrollTracker, proposed_stake: float, active_exposure: float = 0.0) -> FailSafeResult:
        reasons: list[str] = []
        if proposed_stake > Config.MAX_TRADE_RISK:
            reasons.append("exceeds_max_trade_risk")
        if active_exposure + proposed_stake > Config.MAX_TOTAL_EXPOSURE:
            reasons.append("exceeds_total_exposure")
        if tracker.daily_pnl <= -Config.DRAWDOWN_DAILY_LIMIT:
            reasons.append("daily_drawdown_limit_hit")
        if tracker.weekly_pnl <= -Config.DRAWDOWN_WEEKLY_LIMIT:
            reasons.append("weekly_drawdown_limit_hit")
        return FailSafeResult(allowed=not reasons, reasons=reasons)
