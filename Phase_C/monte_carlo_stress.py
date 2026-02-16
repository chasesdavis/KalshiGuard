"""Risk stress tests via Monte Carlo.

The phase gate requires 0% estimated ruin probability for proposed entries.
"""
from __future__ import annotations

from dataclasses import dataclass

from Shared.monte_carlo import MonteCarloSummary, simulate_binary_contract


@dataclass(frozen=True)
class StressTestResult:
    passed: bool
    summary: MonteCarloSummary


class MonteCarloStressTester:
    """Runs trial-based stress checks for position proposals."""

    def run(
        self,
        probability_yes: float,
        stake_dollars: float,
        entry_price_cents: float,
        trials: int = 1_000,
        starting_bankroll: float = 50.0,
    ) -> StressTestResult:
        if stake_dollars <= 0:
            empty = MonteCarloSummary(ruin_probability=0.0, average_pnl=0.0, percentile_05_pnl=0.0, percentile_95_pnl=0.0)
            return StressTestResult(passed=False, summary=empty)

        summary = simulate_binary_contract(
            trials=trials,
            probability_yes=probability_yes,
            stake_dollars=stake_dollars,
            entry_price_cents=entry_price_cents,
            starting_bankroll=starting_bankroll,
        )
        return StressTestResult(passed=summary.ruin_probability <= 0.0, summary=summary)
