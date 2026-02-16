"""Phase C stress testing orchestration."""
from __future__ import annotations

from dataclasses import dataclass

from Shared.config import Config
from Shared.monte_carlo import MonteCarloSummary, simulate_bankroll_paths


@dataclass(frozen=True)
class StressTestReport:
    simulations: int
    steps: int
    ruin_probability: float
    p5_terminal: float
    p50_terminal: float
    p95_terminal: float
    pass_threshold: bool


class MonteCarloStressTester:
    """Runs 1000-simulation stress checks for proposed risk."""

    def run(
        self,
        *,
        bankroll: float,
        risk_amount: float,
        win_probability: float,
        payout_multiple: float,
        simulations: int = 1000,
        steps: int = 25,
    ) -> StressTestReport:
        risk_fraction = 0.0 if bankroll <= 0 else min(max(risk_amount / bankroll, 0.0), 1.0)

        summary: MonteCarloSummary = simulate_bankroll_paths(
            initial_bankroll=bankroll,
            risk_fraction=risk_fraction,
            win_probability=win_probability,
            payout_multiple=payout_multiple,
            simulations=simulations,
            steps=steps,
            ruin_threshold=Config.MIN_BUYING_POWER,
        )

        # Strict preservation gate: ruin probability must stay below 5%.
        pass_threshold = summary.ruin_probability < Config.MAX_RUIN_PROBABILITY
        return StressTestReport(
            simulations=simulations,
            steps=steps,
            ruin_probability=round(summary.ruin_probability, 6),
            p5_terminal=round(summary.p5_terminal, 4),
            p50_terminal=round(summary.p50_terminal, 4),
            p95_terminal=round(summary.p95_terminal, 4),
            pass_threshold=pass_threshold,
        )
