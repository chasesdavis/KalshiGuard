"""Generic Monte Carlo helpers shared across risk and simulation modules."""
from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class MonteCarloSummary:
    ruin_probability: float
    average_pnl: float
    percentile_05_pnl: float
    percentile_95_pnl: float


def simulate_binary_contract(
    trials: int,
    probability_yes: float,
    stake_dollars: float,
    entry_price_cents: float,
    starting_bankroll: float = 50.0,
    seed: int = 7,
) -> MonteCarloSummary:
    """Run binary payout simulations for a contract buying one side at entry price.

    Returns summary on PnL outcomes for stake-sized position equivalent.
    """
    rng = random.Random(seed)
    outcomes: list[float] = []

    if stake_dollars <= 0:
        return MonteCarloSummary(ruin_probability=0.0, average_pnl=0.0, percentile_05_pnl=0.0, percentile_95_pnl=0.0)

    contracts = stake_dollars / max(entry_price_cents / 100.0, 0.01)
    per_contract_win = (100 - entry_price_cents) / 100.0
    per_contract_loss = entry_price_cents / 100.0

    for _ in range(trials):
        yes_occurs = rng.random() < probability_yes
        pnl = contracts * per_contract_win if yes_occurs else -contracts * per_contract_loss
        outcomes.append(round(pnl, 6))

    ordered = sorted(outcomes)
    ruin = sum(1 for val in outcomes if (starting_bankroll + val) <= 0.0) / len(outcomes)
    avg = sum(outcomes) / len(outcomes)
    p05 = ordered[max(0, int(0.05 * len(ordered)) - 1)]
    p95 = ordered[min(len(ordered) - 1, int(0.95 * len(ordered)) - 1)]
    return MonteCarloSummary(
        ruin_probability=round(ruin, 6),
        average_pnl=round(avg, 6),
        percentile_05_pnl=round(p05, 6),
        percentile_95_pnl=round(p95, 6),
    )
