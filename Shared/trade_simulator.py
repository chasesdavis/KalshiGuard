"""Trade simulation lifecycle utilities for paper execution."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulatedTrade:
    ticker: str
    side: str
    contracts: float
    entry_price_cents: float
    exit_price_cents: float
    resolved_yes: bool
    stake_dollars: float
    pnl_dollars: float


class TradeSimulator:
    """Simulate fill, exit, and final resolution for a binary market position."""

    @staticmethod
    def simulate_resolution(
        ticker: str,
        side: str,
        stake_dollars: float,
        entry_price_cents: float,
        probability_yes: float,
        slippage_bps: float = 30.0,
    ) -> SimulatedTrade:
        side = side.upper()
        execution_price = TradeSimulator._apply_slippage(entry_price_cents, side, slippage_bps)
        contracts = stake_dollars / max(execution_price / 100.0, 0.01)
        resolved_yes = probability_yes >= 0.5

        if side == "YES":
            win = resolved_yes
            payout = 100.0 if win else 0.0
        else:
            win = not resolved_yes
            payout = 100.0 if win else 0.0

        pnl = contracts * ((payout - execution_price) / 100.0)
        return SimulatedTrade(
            ticker=ticker,
            side=side,
            contracts=round(contracts, 4),
            entry_price_cents=round(execution_price, 4),
            exit_price_cents=round(payout, 4),
            resolved_yes=resolved_yes,
            stake_dollars=round(stake_dollars, 4),
            pnl_dollars=round(pnl, 4),
        )

    @staticmethod
    def _apply_slippage(price_cents: float, side: str, slippage_bps: float) -> float:
        slip = price_cents * (slippage_bps / 10_000)
        if side == "YES":
            return min(99.0, price_cents + slip)
        return min(99.0, price_cents + slip)
