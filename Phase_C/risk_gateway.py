"""Risk gateway that combines sizing, fail-safe checks, stress testing, and Phase F self-review."""
from __future__ import annotations

from dataclasses import dataclass

from Phase_C.fail_safes import FailSafeEvaluator, FailSafeReport
from Phase_C.kelly_sizing import FractionalKellySizer, PositionSizeDecision
from Phase_C.monte_carlo_stress import MonteCarloStressTester, StressTestReport
from Phase_F.governance_engine import GovernanceEngine, GovernanceReport
from Shared.bankroll_tracker import BankrollTracker
from Shared.config import Config
from Shared.models import PriceSnapshot


@dataclass(frozen=True)
class RiskAssessment:
    ticker: str
    side: str
    bankroll: float
    buying_power: float
    sizing: PositionSizeDecision
    fail_safe_report: FailSafeReport
    stress_test: StressTestReport
    approved: bool
    blockers: list[str]


@dataclass(frozen=True)
class RiskDecision:
    """Lightweight decision payload for approval-gated execution."""

    approved: bool
    reason: str
    contracts: int
    max_risk: float


@dataclass(frozen=True)
class LegacyRiskDecision:
    """Phase D-compatible risk shape retained for older interfaces."""

    approved: bool
    proposed_stake: float
    kelly_fraction: float
    fail_safe_reasons: list[str]
    stress_passed: bool
    ruin_probability: float
    average_pnl: float
    risk_assessment: RiskAssessment


class RiskGateway:
    """Central Phase C decisioning object for pre-trade risk assessment."""

    def __init__(self, tracker: BankrollTracker | None = None) -> None:
        self.tracker = tracker or BankrollTracker()
        self.sizer = FractionalKellySizer()
        self.fail_safes = FailSafeEvaluator()
        self.stress_tester = MonteCarloStressTester()
        self.governance_engine = GovernanceEngine()
        self.kelly_scale_factor = 1.0

    def assess(
        self,
        snapshot_or_signal,
        side_or_snapshot=None,
        ensemble_yes: float | None = None,
        bankroll: float = Config.BANKROLL_START,
    ):
        # Phase E compatibility mode: assess(signal, snapshot[, bankroll]) -> RiskDecision
        if isinstance(snapshot_or_signal, PriceSnapshot) is False:
            signal = snapshot_or_signal
            snapshot = side_or_snapshot
            side = signal.side if signal.side in {"YES", "NO"} else "HOLD"
            if side == "HOLD":
                return RiskDecision(False, "Hold/no-trade signal.", 0, 0.0)
            price = snapshot.yes_ask if side == "YES" else snapshot.no_ask
            contracts = max(1, int(Config.MAX_TRADE_RISK / max(price / 100.0, 0.01)))
            return RiskDecision(True, "Pass", contracts, Config.MAX_TRADE_RISK)

        snapshot = snapshot_or_signal
        side = side_or_snapshot
        if ensemble_yes is None:
            raise ValueError("ensemble_yes is required for RiskAssessment mode")
        return self.assess_snapshot(snapshot, side, ensemble_yes)

    def assess_snapshot(self, snapshot: PriceSnapshot, side: str, ensemble_yes: float) -> RiskAssessment:
        
        fail_safe_report = self.fail_safes.evaluate(
            snapshot=snapshot,
            buying_power=self.tracker.buying_power,
            daily_loss=self.tracker.daily_loss,
            weekly_loss=self.tracker.weekly_loss,
        )

        effective_multiplier = self.tracker.kelly_multiplier * self.kelly_scale_factor
        sizing = self.sizer.size_risk(
            side=side,
            prob_yes=ensemble_yes,
            bankroll=self.tracker.current_bankroll,
            kelly_multiplier=effective_multiplier,
            exposure_cap_remaining=self.tracker.exposure_capacity,
        )

        p_win = ensemble_yes if side == "YES" else 1 - ensemble_yes
        price = snapshot.yes_ask / 100.0 if side == "YES" else snapshot.no_ask / 100.0
        payout_multiple = 0.0 if price <= 0 else (1 - price) / price

        stress = self.stress_tester.run(
            bankroll=self.tracker.current_bankroll,
            risk_amount=sizing.recommended_risk,
            win_probability=p_win,
            payout_multiple=payout_multiple,
            simulations=Config.MONTE_CARLO_SIMS,
        )

        blockers: list[str] = []
        if side == "HOLD":
            blockers.append("no_trade_signal")
        if sizing.recommended_risk <= 0:
            blockers.append("zero_position_size")
        if not fail_safe_report.approved:
            blockers.extend(fail_safe_report.reasons)
        if not stress.pass_threshold:
            blockers.append("stress_test_ruin_probability")

        approved = len(blockers) == 0

        return RiskAssessment(
            ticker=snapshot.ticker,
            side=side,
            bankroll=self.tracker.current_bankroll,
            buying_power=self.tracker.buying_power,
            sizing=sizing,
            fail_safe_report=fail_safe_report,
            stress_test=stress,
            approved=approved,
            blockers=blockers,
        )

    def run_self_review(self) -> GovernanceReport:
        """Apply governance policy and update Kelly scaling in-memory."""
        report = self.governance_engine.run_self_review(
            daily_loss=self.tracker.daily_loss,
            weekly_loss=self.tracker.weekly_loss,
        )
        self.kelly_scale_factor = report.adjustment.kelly_scale_factor
        return report

    def assess_trade(
        self,
        bankroll_tracker: BankrollTracker,
        probability_yes: float,
        entry_price_cents: float,
        active_exposure: float = 0.0,
        trials: int = 1000,
    ) -> LegacyRiskDecision:
        """Backward-compatible Phase D risk API.

        `probability_yes` is interpreted as the win probability for the proposed side.
        """

        # Keep tracker in sync with caller-provided exposure and drawdown aliases.
        bankroll_tracker.open_exposure = active_exposure
        daily_loss = bankroll_tracker.daily_loss
        weekly_loss = bankroll_tracker.weekly_loss
        if hasattr(bankroll_tracker, "daily_pnl"):
            daily_loss = max(daily_loss, max(-float(bankroll_tracker.daily_pnl), 0.0))
        if hasattr(bankroll_tracker, "weekly_pnl"):
            weekly_loss = max(weekly_loss, max(-float(bankroll_tracker.weekly_pnl), 0.0))

        side = "YES" if probability_yes >= 0.5 else "NO"
        p_win = min(max(probability_yes, 0.0), 1.0)

        fail_safe_report = self.fail_safes.evaluate(
            snapshot=PriceSnapshot(
                ticker="SIMULATED",
                timestamp="",
                yes_bid=max(1.0, entry_price_cents - 2),
                yes_ask=entry_price_cents,
                no_bid=max(1.0, 100 - entry_price_cents - 2),
                no_ask=max(1.0, 100 - entry_price_cents),
                volume=10_000,
                open_interest=100_000,
            ),
            buying_power=bankroll_tracker.buying_power,
            daily_loss=daily_loss,
            weekly_loss=weekly_loss,
        )

        effective_multiplier = bankroll_tracker.kelly_multiplier * self.kelly_scale_factor
        sizing = self.sizer.size_risk(
            side=side,
            prob_yes=p_win if side == "YES" else 1 - p_win,
            bankroll=bankroll_tracker.current_bankroll,
            kelly_multiplier=effective_multiplier,
            exposure_cap_remaining=bankroll_tracker.exposure_capacity,
        )

        price = max(entry_price_cents / 100.0, 0.01)
        payout_multiple = (1 - price) / price
        stress = self.stress_tester.run(
            bankroll=bankroll_tracker.current_bankroll,
            risk_amount=sizing.recommended_risk,
            win_probability=p_win,
            payout_multiple=payout_multiple,
            simulations=trials,
            steps=Config.MONTE_CARLO_STEPS,
        )

        blockers: list[str] = []
        if sizing.recommended_risk <= 0:
            blockers.append("zero_position_size")
        if not fail_safe_report.approved:
            blockers.extend(fail_safe_report.reasons)
        if not stress.pass_threshold:
            blockers.append("stress_test_ruin_probability")

        approved = len(blockers) == 0
        average_pnl = round(sizing.recommended_risk * ((p_win * payout_multiple) - (1 - p_win)), 6)

        risk_assessment = RiskAssessment(
            ticker="SIMULATED",
            side=side,
            bankroll=bankroll_tracker.current_bankroll,
            buying_power=bankroll_tracker.buying_power,
            sizing=sizing,
            fail_safe_report=fail_safe_report,
            stress_test=stress,
            approved=approved,
            blockers=blockers,
        )
        return LegacyRiskDecision(
            approved=approved,
            proposed_stake=sizing.recommended_risk,
            kelly_fraction=sizing.kelly_fraction_applied,
            fail_safe_reasons=fail_safe_report.reasons,
            stress_passed=stress.pass_threshold,
            ruin_probability=stress.ruin_probability,
            average_pnl=average_pnl,
            risk_assessment=risk_assessment,
        )
