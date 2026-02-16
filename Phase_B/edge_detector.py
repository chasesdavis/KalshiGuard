"""Edge detection and EV gating for Phase B."""
from __future__ import annotations

from dataclasses import dataclass

from Phase_B.probability_engine import ProbabilityEstimate
from Shared.config import Config
from Shared.models import PriceSnapshot


@dataclass(frozen=True)
class EdgeDecision:
    ticker: str
    side: str
    ev_percent: float
    confirmations: list[str]
    confirmation_count: int
    threshold_checks: dict[str, bool]


class EdgeDetector:
    """Detect and validate edges with strict confirmation and EV gates."""

    def evaluate(self, snapshot: PriceSnapshot, estimate: ProbabilityEstimate, confidence: float) -> EdgeDecision:
        yes_ev_pct = self._ev_percent_yes(snapshot.yes_ask, estimate.ensemble_yes)
        no_ev_pct = self._ev_percent_no(snapshot.no_ask, estimate.ensemble_yes)

        side = "YES" if yes_ev_pct >= no_ev_pct else "NO"
        ev_pct = max(yes_ev_pct, no_ev_pct)
        confirmations = self._build_confirmations(snapshot, estimate, yes_ev_pct, no_ev_pct)

        threshold_checks = {
            "min_ev": ev_pct >= (Config.MIN_EV_THRESHOLD * 100),
            "min_confirmations": len(confirmations) >= Config.MIN_CONFIRMATIONS,
            "min_confidence": confidence >= Config.MIN_CONFIDENCE,
        }

        if not all(threshold_checks.values()):
            side = "HOLD"

        return EdgeDecision(
            ticker=snapshot.ticker,
            side=side,
            ev_percent=ev_pct,
            confirmations=confirmations,
            confirmation_count=len(confirmations),
            threshold_checks=threshold_checks,
        )

    @staticmethod
    def _ev_percent_yes(yes_ask: float, prob_yes: float) -> float:
        expected_cents = (prob_yes * (100 - yes_ask)) - ((1 - prob_yes) * yes_ask)
        if yes_ask <= 0:
            return -100.0
        return (expected_cents / yes_ask) * 100

    @staticmethod
    def _ev_percent_no(no_ask: float, prob_yes: float) -> float:
        prob_no = 1 - prob_yes
        expected_cents = (prob_no * (100 - no_ask)) - ((1 - prob_no) * no_ask)
        if no_ask <= 0:
            return -100.0
        return (expected_cents / no_ask) * 100

    @staticmethod
    def _build_confirmations(
        snapshot: PriceSnapshot,
        estimate: ProbabilityEstimate,
        yes_ev_pct: float,
        no_ev_pct: float,
    ) -> list[str]:
        confirmations: list[str] = []
        if abs(estimate.external_yes - estimate.market_implied_yes) >= 0.03:
            confirmations.append("external_calibration_gap")
        if abs(estimate.bayesian_yes - estimate.market_implied_yes) >= 0.02:
            confirmations.append("bayesian_repricing")
        if estimate.model_agreement >= 0.88:
            confirmations.append("ensemble_agreement")
        if snapshot.volume >= 5_000:
            confirmations.append("liquidity_check")
        if (snapshot.yes_ask - snapshot.yes_bid) <= 4:
            confirmations.append("tight_spread")
        if max(yes_ev_pct, no_ev_pct) >= 5.0:
            confirmations.append("positive_raw_ev")
        return confirmations
