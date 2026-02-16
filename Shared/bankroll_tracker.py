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
