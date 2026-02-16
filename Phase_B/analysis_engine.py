"""Phase B orchestration for explainable EV analysis and Phase E proposals."""
from __future__ import annotations

from dataclasses import dataclass

from Phase_B.edge_detector import EdgeDecision, EdgeDetector
from Phase_B.external_data import ExternalDataProvider
from Phase_B.probability_engine import ProbabilityEngine, ProbabilityEstimate
from Phase_C.imessage_proposal import REGISTRY, TradeProposal
from Phase_C.risk_gateway import RiskDecision, RiskGateway
from Shared.models import EVSignal, PriceSnapshot


@dataclass(frozen=True)
class AnalysisResult:
    """Full Phase B analysis payload for API and logging."""

    signal: EVSignal
    probability_estimate: ProbabilityEstimate
    edge_decision: EdgeDecision
    external_payload: dict


@dataclass(frozen=True)
class ProposalResult:
    """Composite payload for live proposal flow."""

    analysis: AnalysisResult
    risk: RiskDecision
    proposal: TradeProposal | None


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

        explanation = self._build_explanation(snapshot, estimate, decision, external_payload)
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
        )

    def propose_trade(self, snapshot: PriceSnapshot) -> ProposalResult:
        """Analyze, risk-check, and (if approved by risk) send human approval proposal."""
        analysis = self.analyze_snapshot(snapshot)
        risk = self.risk_gateway.assess(analysis.signal, snapshot)
        proposal = REGISTRY.create_and_send(analysis.signal, snapshot, risk) if risk.approved else None
        return ProposalResult(analysis=analysis, risk=risk, proposal=proposal)

    @staticmethod
    def _build_explanation(
        snapshot: PriceSnapshot,
        estimate: ProbabilityEstimate,
        decision: EdgeDecision,
        external_payload: dict,
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
            f"- Side: {decision.side} | EV: {decision.ev_percent:.2f}%\n"
            f"- Sources: {source_names}"
        )
