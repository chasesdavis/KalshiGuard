"""Governance logic for weekly risk-first self-review."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PerformanceSnapshot:
    trade_count: int
    wins: int
    losses: int
    total_pnl: float
    max_drawdown: float
    daily_loss: float
    weekly_loss: float


@dataclass(frozen=True)
class GovernanceAdjustment:
    kelly_scale_factor: float
    min_confidence_delta: float
    min_ev_delta: float
    risk_mode: str
    rationale: list[str]


class GovernancePolicy:
    """Computes conservative parameter adjustments from recent performance."""

    def evaluate(self, perf: PerformanceSnapshot) -> GovernanceAdjustment:
        rationale: list[str] = []
        kelly_scale = 1.0
        min_conf_delta = 0.0
        min_ev_delta = 0.0
        risk_mode = "normal"

        win_rate = (perf.wins / perf.trade_count) if perf.trade_count > 0 else 0.5

        if perf.max_drawdown >= 2.0 or perf.weekly_loss >= 0.8:
            kelly_scale *= 0.5
            min_conf_delta += 0.01
            min_ev_delta += 0.05
            risk_mode = "capital_preservation"
            rationale.append("High drawdown detected; halving Kelly exposure.")

        if perf.daily_loss >= 0.20:
            kelly_scale *= 0.7
            min_conf_delta += 0.005
            rationale.append("Daily loss elevated; reducing sizing further.")

        if perf.trade_count >= 20 and win_rate < 0.50:
            kelly_scale *= 0.85
            min_ev_delta += 0.03
            rationale.append("Sub-50% win rate over sample; tightening edge threshold.")

        if perf.total_pnl > 1.5 and perf.max_drawdown < 0.5 and win_rate >= 0.58:
            kelly_scale = min(kelly_scale * 1.05, 1.10)
            rationale.append("Stable positive performance; slight measured sizing unlock.")

        if not rationale:
            rationale.append("Performance stable; no policy changes required.")

        return GovernanceAdjustment(
            kelly_scale_factor=round(max(min(kelly_scale, 1.10), 0.40), 4),
            min_confidence_delta=round(min_conf_delta, 4),
            min_ev_delta=round(min_ev_delta, 4),
            risk_mode=risk_mode,
            rationale=rationale,
        )
