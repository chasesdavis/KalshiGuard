"""Bankroll state utilities for micro-bankroll risk controls.

Phase C keeps this tracker read-only for proposal calculations.
"""
from __future__ import annotations

from dataclasses import dataclass

from Shared.config import Config


@dataclass
class BankrollTracker:
    """Tracks bankroll, buying power, and drawdown-relevant metrics."""

    starting_bankroll: float = Config.BANKROLL_START
    realized_pnl: float = 0.0
    open_exposure: float = 0.0
    daily_loss: float = 0.0
    weekly_loss: float = 0.0
    max_drawdown_pct: float = 0.0
    _peak_bankroll: float = 0.0

    def __post_init__(self) -> None:
        self._peak_bankroll = self.current_bankroll

    @property
    def current_bankroll(self) -> float:
        return round(self.starting_bankroll + self.realized_pnl, 4)

    @property
    def buying_power(self) -> float:
        return round(max(self.current_bankroll - self.open_exposure, 0.0), 4)

    @property
    def growth_ratio(self) -> float:
        if self.starting_bankroll <= 0:
            return 1.0
        return self.current_bankroll / self.starting_bankroll

    @property
    def kelly_multiplier(self) -> float:
        """Dynamic scaling from 0.10x to 0.25x after +20% growth.

        Before +20% growth: capped at 0.10x.
        At/above +20% growth: 0.25x.
        """

        return Config.KELLY_GROWTH_MULTIPLIER if self.growth_ratio >= Config.GROWTH_UNLOCK_RATIO else Config.KELLY_BASE_MULTIPLIER

    @property
    def exposure_capacity(self) -> float:
        return round(max(Config.MAX_TOTAL_EXPOSURE - self.open_exposure, 0.0), 4)

    @property
    def daily_pnl(self) -> float:
        """Backward-compatible pnl view used by older risk tests."""
        return -self.daily_loss

    @daily_pnl.setter
    def daily_pnl(self, value: float) -> None:
        self.daily_loss = max(-value, 0.0)

    @property
    def weekly_pnl(self) -> float:
        return -self.weekly_loss

    @weekly_pnl.setter
    def weekly_pnl(self, value: float) -> None:
        self.weekly_loss = max(-value, 0.0)

    def apply_pnl(self, pnl_dollars: float) -> None:
        """Apply realized PnL and update drawdown metrics."""
        self.realized_pnl = round(self.realized_pnl + pnl_dollars, 4)
        if pnl_dollars < 0:
            self.daily_loss = round(self.daily_loss + abs(pnl_dollars), 4)
            self.weekly_loss = round(self.weekly_loss + abs(pnl_dollars), 4)

        current = self.current_bankroll
        self._peak_bankroll = max(self._peak_bankroll, current)
        if self._peak_bankroll > 0:
            drawdown = max((self._peak_bankroll - current) / self._peak_bankroll * 100.0, 0.0)
            self.max_drawdown_pct = round(max(self.max_drawdown_pct, drawdown), 4)
