"""Bankroll tracking utilities for simulation and risk enforcement."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BankrollTracker:
    """Tracks current bankroll and historical equity curve for drawdown checks."""

    starting_bankroll: float = 50.0

    def __post_init__(self) -> None:
        self.current_bankroll = float(self.starting_bankroll)
        self.peak_bankroll = float(self.starting_bankroll)
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.trade_count = 0

    def apply_pnl(self, pnl_dollars: float) -> None:
        self.current_bankroll = round(max(0.0, self.current_bankroll + pnl_dollars), 4)
        self.peak_bankroll = max(self.peak_bankroll, self.current_bankroll)
        self.daily_pnl = round(self.daily_pnl + pnl_dollars, 4)
        self.weekly_pnl = round(self.weekly_pnl + pnl_dollars, 4)
        self.trade_count += 1

    def reset_daily(self) -> None:
        self.daily_pnl = 0.0

    def reset_weekly(self) -> None:
        self.weekly_pnl = 0.0

    @property
    def max_drawdown_abs(self) -> float:
        return round(max(0.0, self.peak_bankroll - self.current_bankroll), 4)

    @property
    def max_drawdown_pct(self) -> float:
        if self.peak_bankroll <= 0:
            return 0.0
        return round((self.max_drawdown_abs / self.peak_bankroll) * 100, 4)
