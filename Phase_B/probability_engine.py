"""Phase B probability engine.

Combines market-implied prices, external calibration anchors, and lightweight
internal signals into a conservative ensemble probability estimate.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean

from Phase_B.external_data import ExternalAnchor
from Shared.models import PriceSnapshot


@dataclass(frozen=True)
class ProbabilityEstimate:
    """Ensemble probability output with component diagnostics."""

    ticker: str
    market_implied_yes: float
    external_yes: float
    bayesian_yes: float
    internal_yes: float
    ensemble_yes: float
    model_agreement: float


class ProbabilityEngine:
    """Compute conservative YES probabilities from several low-latency components."""

    def estimate_yes_probability(
        self,
        snapshot: PriceSnapshot,
        anchors: list[ExternalAnchor],
    ) -> ProbabilityEstimate:
        market_implied = self._market_implied(snapshot)
        external_yes = self._external_consensus(anchors)
        bayesian_yes = self._bayesian_blend(market_implied, external_yes, anchors)
        internal_yes = self._internal_signal(snapshot, market_implied)

        ensemble_yes = (
            0.35 * market_implied
            + 0.30 * external_yes
            + 0.25 * bayesian_yes
            + 0.10 * internal_yes
        )
        components = [market_implied, external_yes, bayesian_yes, internal_yes]
        model_agreement = 1.0 - (max(components) - min(components))

        return ProbabilityEstimate(
            ticker=snapshot.ticker,
            market_implied_yes=market_implied,
            external_yes=external_yes,
            bayesian_yes=bayesian_yes,
            internal_yes=internal_yes,
            ensemble_yes=min(max(ensemble_yes, 0.01), 0.99),
            model_agreement=min(max(model_agreement, 0.0), 1.0),
        )

    @staticmethod
    def _market_implied(snapshot: PriceSnapshot) -> float:
        mid_yes = (snapshot.yes_bid + snapshot.yes_ask) / 2
        return min(max(mid_yes / 100.0, 0.01), 0.99)

    @staticmethod
    def _external_consensus(anchors: list[ExternalAnchor]) -> float:
        weighted = [a.probability_yes * a.confidence for a in anchors]
        total_conf = sum(a.confidence for a in anchors)
        if total_conf <= 0:
            return 0.50
        return min(max(sum(weighted) / total_conf, 0.01), 0.99)

    @staticmethod
    def _bayesian_blend(market_implied: float, external_yes: float, anchors: list[ExternalAnchor]) -> float:
        # Treat external consensus confidence as pseudo-observations.
        prior_alpha = 1 + (market_implied * 8)
        prior_beta = 1 + ((1 - market_implied) * 8)
        ext_strength = max(sum(a.confidence for a in anchors), 0.1) * 4
        post_alpha = prior_alpha + external_yes * ext_strength
        post_beta = prior_beta + (1 - external_yes) * ext_strength
        return min(max(post_alpha / (post_alpha + post_beta), 0.01), 0.99)

    @staticmethod
    def _internal_signal(snapshot: PriceSnapshot, market_implied: float) -> float:
        # Mild adjustments only; capital preservation favors low sensitivity.
        spread_penalty = max(0.0, (snapshot.yes_ask - snapshot.yes_bid) / 100)
        depth_bias = ((snapshot.yes_bid - snapshot.no_bid) / 100) * 0.15
        liquidity_bonus = min(snapshot.volume / 200_000, 1.0) * 0.03
        internal = market_implied + depth_bias + liquidity_bonus - spread_penalty
        return min(max(internal, 0.01), 0.99)

    @staticmethod
    def aggregate_confidence(estimate: ProbabilityEstimate, anchors: list[ExternalAnchor]) -> float:
        """Confidence score for minimum-gate checks."""
        anchor_conf = fmean([a.confidence for a in anchors]) if anchors else 0.4
        confidence = 0.45 * estimate.model_agreement + 0.35 * anchor_conf + 0.20
        return min(max(confidence, 0.0), 0.99)
