"""Phase B orchestration for explainable EV analysis and paper-trade proposals."""
from __future__ import annotations

from dataclasses import dataclass

from Phase_B.edge_detector import EdgeDecision, EdgeDetector
from Phase_B.external_data import ExternalDataProvider
from Phase_B.probability_engine import ProbabilityEngine, ProbabilityEstimate
from Phase_C.risk_gateway import RiskAssessment, RiskGateway
from Shared.bankroll_tracker import BankrollTracker
from Shared.models import EVSignal, PriceSnapshot


@dataclass(frozen=True)
class PaperTradeProposal:
    """Phase B output for Phase D paper-trading candidate."""

    ticker: str
    side: str
    entry_price_cents: float
    probability_yes: float
    approved_by_risk: bool
    proposed_stake: float
    risk_reasons: list[str]
    generation_mode: str


@dataclass(frozen=True)
class AnalysisResult:
    """Full Phase B analysis payload for API and logging."""

    signal: EVSignal
    probability_estimate: ProbabilityEstimate
    edge_decision: EdgeDecision
    external_payload: dict
    snapshot: PriceSnapshot
    risk_assessment: RiskAssessment
    paper_trade_proposal: PaperTradeProposal


class PhaseBAnalysisEngine:
    """High-level engine that computes edge and explanation for one market snapshot."""

    def __init__(self) -> None:
        self.external_data = ExternalDataProvider()
        self.probability_engine = ProbabilityEngine()
        self.edge_detector = EdgeDetector()
        self.risk_gateway = RiskGateway()

    def analyze_snapshot(self, snapshot: PriceSnapshot) -> AnalysisResult:
        anchors = self.external_data.get_probability_anchors(snapshot.ticker)
        external_payload = self.external_data.get_source_payload(snapshot.ticker)
        estimate = self.probability_engine.estimate_yes_probability(snapshot, anchors)
        confidence = self.probability_engine.aggregate_confidence(estimate, anchors)
        decision = self.edge_detector.evaluate(snapshot, estimate, confidence)

        proposal_side, mode = self._select_paper_side(decision, estimate)
        proposal_entry = snapshot.yes_ask if proposal_side == "YES" else snapshot.no_ask

        risk_assessment = self.risk_gateway.assess_trade(
            bankroll_tracker=BankrollTracker(starting_bankroll=50.0),
            probability_yes=estimate.ensemble_yes,
            entry_price_cents=proposal_entry,
        )

        proposal = PaperTradeProposal(
            ticker=snapshot.ticker,
            side=proposal_side,
            entry_price_cents=proposal_entry,
            probability_yes=round(estimate.ensemble_yes, 4),
            approved_by_risk=risk_assessment.approved,
            proposed_stake=risk_assessment.proposed_stake,
            risk_reasons=risk_assessment.fail_safe_reasons,
            generation_mode=mode,
        )

        explanation = self._build_explanation(snapshot, estimate, decision, external_payload, risk_assessment, proposal)
        signal = EVSignal(
            ticker=snapshot.ticker,
            ev_percent=round(decision.ev_percent, 2),
            confidence=round(confidence, 4),
            explanation=explanation,
            data_sources=[s["name"] for s in external_payload["sources"]],
            side=decision.side,
        )
        return AnalysisResult(
            signal=signal,
            probability_estimate=estimate,
            edge_decision=decision,
            external_payload=external_payload,
            snapshot=snapshot,
            risk_assessment=risk_assessment,
            paper_trade_proposal=proposal,
        )

    @staticmethod
    def _select_paper_side(decision: EdgeDecision, estimate: ProbabilityEstimate) -> tuple[str, str]:
        """Select a simulation side.

        In Phase D we still simulate HOLD candidates by using ensemble repricing direction,
        while preserving strict Phase B live side gating in `edge_decision.side`.
        """
        if decision.side in {"YES", "NO"}:
            return decision.side, "edge_confirmed"

        repricing_side = "YES" if estimate.ensemble_yes >= estimate.market_implied_yes else "NO"
        return repricing_side, "repricing_fallback"

    @staticmethod
    def _build_explanation(
        snapshot: PriceSnapshot,
        estimate: ProbabilityEstimate,
        decision: EdgeDecision,
        external_payload: dict,
        risk_assessment: RiskAssessment,
        proposal: PaperTradeProposal,
    ) -> str:
        source_names = ", ".join(s["name"] for s in external_payload["sources"])
        return (
            f"Phase B Analysis for {snapshot.ticker}\n"
            f"- Market implied YES: {estimate.market_implied_yes:.1%}\n"
            f"- External consensus YES: {estimate.external_yes:.1%}\n"
            f"- Bayesian YES: {estimate.bayesian_yes:.1%}\n"
            f"- Internal signal YES: {estimate.internal_yes:.1%}\n"
            f"- Ensemble YES: {estimate.ensemble_yes:.1%}\n"
            f"- Confirmations ({decision.confirmation_count}): {', '.join(decision.confirmations) or 'none'}\n"
            f"- Threshold checks: {decision.threshold_checks}\n"
            f"- Live side gate: {decision.side} | EV: {decision.ev_percent:.2f}%\n"
            f"- Paper side: {proposal.side} ({proposal.generation_mode}) @ {proposal.entry_price_cents:.2f}c\n"
            f"- Risk approved: {risk_assessment.approved} | stake=${risk_assessment.proposed_stake:.2f} | ruin={risk_assessment.ruin_probability:.4f}\n"
            f"- Sources: {source_names}"
        )
