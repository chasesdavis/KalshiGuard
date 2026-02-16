"""Shared Monte Carlo helpers for bankroll stress testing."""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class MonteCarloSummary:
    ruin_probability: float
    p5_terminal: float
    p50_terminal: float
    p95_terminal: float


def simulate_bankroll_paths(
    *,
    initial_bankroll: float,
    risk_fraction: float,
    win_probability: float,
    payout_multiple: float,
    simulations: int = 1000,
    steps: int = 25,
    ruin_threshold: float = 40.0,
    seed: int = 7,
) -> MonteCarloSummary:
    """Simulate repeated micro-trades and report tail risk statistics."""

    rng = random.Random(seed)
    terminals: list[float] = []
    ruins = 0

    bounded_win_prob = min(max(win_probability, 0.0), 1.0)
    bounded_risk_fraction = max(risk_fraction, 0.0)

    for _ in range(simulations):
        bankroll = initial_bankroll
        for _ in range(steps):
            stake = bankroll * bounded_risk_fraction
            if stake <= 0:
                continue

            if rng.random() <= bounded_win_prob:
                bankroll += stake * payout_multiple
            else:
                bankroll -= stake

            if bankroll <= ruin_threshold:
                ruins += 1
                break

        terminals.append(bankroll)

    terminals.sort()

    def percentile(pct: float) -> float:
        index = int((len(terminals) - 1) * pct)
        return terminals[index]

    return MonteCarloSummary(
        ruin_probability=ruins / simulations if simulations else 1.0,
        p5_terminal=percentile(0.05),
        p50_terminal=percentile(0.50),
        p95_terminal=percentile(0.95),
    )
