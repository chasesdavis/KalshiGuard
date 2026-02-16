"""Phase B probability engine.

Combines market-implied prices, external calibration anchors, and lightweight
internal signals into a conservative ensemble probability estimate.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import fmean
import json

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

    DEFAULT_WEIGHTS = {
        "market_implied_yes": 0.35,
        "external_yes": 0.30,
        "bayesian_yes": 0.25,
        "internal_yes": 0.10,
    }

    def __init__(self, weights_path: str | Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        self.weights_path = Path(weights_path) if weights_path else base_dir / "Phase_F" / "artifacts" / "probability_weights.json"
        retrain_payload = self._load_retrain_payload()
        self.weights = self._normalize_weights(retrain_payload.get("weights", self.DEFAULT_WEIGHTS))
        self.calibration_bias = float(retrain_payload.get("calibration_bias", 0.0))
        self.calibration_temperature = max(float(retrain_payload.get("calibration_temperature", 1.0)), 0.8)
        self.metadata = retrain_payload.get("metadata", {})

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
            self.weights["market_implied_yes"] * market_implied
            + self.weights["external_yes"] * external_yes
            + self.weights["bayesian_yes"] * bayesian_yes
            + self.weights["internal_yes"] * internal_yes
        )
        ensemble_yes = self._apply_calibration(ensemble_yes)

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

    def apply_retrained_weights(
        self,
        *,
        weights: dict[str, float],
        calibration_bias: float,
        calibration_temperature: float,
        metadata: dict | None = None,
    ) -> None:
        """Persist retrained weights for future ProbabilityEngine initializations."""
        payload = {
            "weights": self._normalize_weights(weights),
            "calibration_bias": float(calibration_bias),
            "calibration_temperature": max(float(calibration_temperature), 0.8),
            "metadata": metadata or {},
        }
        self.weights_path.parent.mkdir(parents=True, exist_ok=True)
        self.weights_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        self.weights = payload["weights"]
        self.calibration_bias = payload["calibration_bias"]
        self.calibration_temperature = payload["calibration_temperature"]
        self.metadata = payload["metadata"]

    def get_retrain_status(self) -> dict:
        return {
            "weights": self.weights,
            "calibration_bias": self.calibration_bias,
            "calibration_temperature": self.calibration_temperature,
            "metadata": self.metadata,
            "weights_path": str(self.weights_path),
        }

    def _load_retrain_payload(self) -> dict:
        if not self.weights_path.exists():
            return {
                "weights": self.DEFAULT_WEIGHTS,
                "calibration_bias": 0.0,
                "calibration_temperature": 1.0,
                "metadata": {"status": "baseline"},
            }
        try:
            payload = json.loads(self.weights_path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _normalize_weights(weights: dict[str, float]) -> dict[str, float]:
        normalized = {k: max(float(weights.get(k, 0.0)), 0.0) for k in ProbabilityEngine.DEFAULT_WEIGHTS}
        total = sum(normalized.values())
        if total <= 0:
            return ProbabilityEngine.DEFAULT_WEIGHTS.copy()
        return {k: round(v / total, 6) for k, v in normalized.items()}

    def _apply_calibration(self, probability: float) -> float:
        centered = (probability - 0.5) / self.calibration_temperature + 0.5
        return min(max(centered + self.calibration_bias, 0.01), 0.99)
