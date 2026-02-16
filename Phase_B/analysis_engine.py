"""Phase B orchestration for explainable EV analysis with Phase C risk context."""
from __future__ import annotations

from dataclasses import dataclass

from Phase_B.edge_detector import EdgeDecision, EdgeDetector
from Phase_B.external_data import ExternalDataProvider
from Phase_B.probability_engine import ProbabilityEngine, ProbabilityEstimate
from Phase_C.imessage_proposal import log_trade_proposal
from Phase_C.risk_gateway import RiskAssessment, RiskGateway
from Shared.models import EVSignal, PriceSnapshot


@dataclass(frozen=True)
class AnalysisResult:
    """Full analysis payload for API and logging."""

    signal: EVSignal
    probability_estimate: ProbabilityEstimate
    edge_decision: EdgeDecision
    external_payload: dict
    risk_assessment: RiskAssessment
    proposal_preview: str


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
        risk_assessment = self.risk_gateway.assess(snapshot, decision.side, estimate.ensemble_yes)
        explanation = self._build_explanation(snapshot, estimate, decision, external_payload, risk_assessment)

        signal = EVSignal(
            ticker=snapshot.ticker,
            ev_percent=round(decision.ev_percent, 2),
            confidence=round(confidence, 4),
            explanation=explanation,
            data_sources=[s["name"] for s in external_payload["sources"]],
            side=decision.side,
        )
        final_result = AnalysisResult(
            signal=signal,
            probability_estimate=estimate,
            edge_decision=decision,
            external_payload=external_payload,
            risk_assessment=risk_assessment,
            proposal_preview="",
        )
        proposal_preview = log_trade_proposal(final_result, risk_assessment)
        return AnalysisResult(
            signal=signal,
            probability_estimate=estimate,
            edge_decision=decision,
            external_payload=external_payload,
            risk_assessment=risk_assessment,
            proposal_preview=proposal_preview,
        )

    @staticmethod
    def _build_explanation(
        snapshot: PriceSnapshot,
        estimate: ProbabilityEstimate,
        decision: EdgeDecision,
        external_payload: dict,
        risk_assessment: RiskAssessment,
    ) -> str:
        source_names = ", ".join(s["name"] for s in external_payload["sources"])
        stress = risk_assessment.stress_test
        return (
            f"Phase B+C Analysis for {snapshot.ticker}\n"
            f"- Market implied YES: {estimate.market_implied_yes:.1%}\n"
            f"- External consensus YES: {estimate.external_yes:.1%}\n"
            f"- Bayesian YES: {estimate.bayesian_yes:.1%}\n"
            f"- Internal signal YES: {estimate.internal_yes:.1%}\n"
            f"- Ensemble YES: {estimate.ensemble_yes:.1%}\n"
            f"- Confirmations ({decision.confirmation_count}): {', '.join(decision.confirmations) or 'none'}\n"
            f"- Threshold checks: {decision.threshold_checks}\n"
            f"- Side: {decision.side} | EV: {decision.ev_percent:.2f}%\n"
            f"- Proposed risk: ${risk_assessment.sizing.recommended_risk:.2f} "
            f"(Kelly={risk_assessment.sizing.kelly_fraction_applied:.4f})\n"
            f"- Stress ruin probability: {stress.ruin_probability:.2%} (n={stress.simulations})\n"
            f"- Fail-safe approved: {risk_assessment.fail_safe_report.approved} | "
            f"Blockers: {', '.join(risk_assessment.blockers) or 'none'}\n"
            f"- Sources: {source_names}"
        )
