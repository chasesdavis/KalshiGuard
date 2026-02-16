"""Unified Phase C risk gateway for trade and paper simulation checks."""
from __future__ import annotations

from dataclasses import dataclass

from Phase_C.fail_safes import FailSafeGate
from Phase_C.kelly_sizing import KellySizer
from Phase_C.monte_carlo_stress import MonteCarloStressTester
from Shared.bankroll_tracker import BankrollTracker


@dataclass(frozen=True)
class RiskAssessment:
    approved: bool
    proposed_stake: float
    kelly_fraction: float
    fail_safe_reasons: list[str]
    stress_passed: bool
    ruin_probability: float
    average_pnl: float


class RiskGateway:
    """Primary risk orchestration entrypoint used by Phase B and D."""

    def __init__(self) -> None:
        self.kelly = KellySizer()
        self.fail_safes = FailSafeGate()
        self.stress = MonteCarloStressTester()

    def assess_trade(
        self,
        bankroll_tracker: BankrollTracker,
        probability_yes: float,
        entry_price_cents: float,
        active_exposure: float = 0.0,
        trials: int = 1000,
    ) -> RiskAssessment:
        kelly_result = self.kelly.size_position(bankroll_tracker.current_bankroll, probability_yes, entry_price_cents)
        fail_safe = self.fail_safes.evaluate(bankroll_tracker, kelly_result.recommended_stake, active_exposure=active_exposure)

        stress_result = self.stress.run(
            probability_yes=probability_yes,
            stake_dollars=kelly_result.recommended_stake,
            entry_price_cents=entry_price_cents,
            trials=trials,
            starting_bankroll=bankroll_tracker.current_bankroll,
        )

        approved = fail_safe.allowed and stress_result.passed
        return RiskAssessment(
            approved=approved,
            proposed_stake=kelly_result.recommended_stake,
            kelly_fraction=kelly_result.kelly_fraction,
            fail_safe_reasons=fail_safe.reasons,
            stress_passed=stress_result.passed,
            ruin_probability=stress_result.summary.ruin_probability,
            average_pnl=stress_result.summary.average_pnl,
        )

    def assess_paper_simulation(
        self,
        bankroll_tracker: BankrollTracker,
        probability_yes: float,
        entry_price_cents: float,
    ) -> RiskAssessment:
        """Convenience alias with lower trial count for route-level responsiveness."""
        return self.assess_trade(
            bankroll_tracker=bankroll_tracker,
            probability_yes=probability_yes,
            entry_price_cents=entry_price_cents,
            trials=500,
        )
