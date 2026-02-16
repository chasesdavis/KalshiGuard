from Phase_B.edge_detector import EdgeDetector
from Phase_B.probability_engine import ProbabilityEstimate
from Shared.models import PriceSnapshot


def test_edge_detector_returns_hold_when_thresholds_fail():
    detector = EdgeDetector()
    snapshot = PriceSnapshot(
        ticker="TEST",
        timestamp="2026-02-15T12:00:00Z",
        yes_bid=48,
        yes_ask=52,
        no_bid=48,
        no_ask=52,
        volume=3000,
        open_interest=10000,
    )
    estimate = ProbabilityEstimate(
        ticker="TEST",
        market_implied_yes=0.50,
        external_yes=0.51,
        bayesian_yes=0.505,
        internal_yes=0.50,
        ensemble_yes=0.505,
        model_agreement=0.99,
    )

    decision = detector.evaluate(snapshot, estimate, confidence=0.95)

    assert decision.side == "HOLD"
    assert decision.threshold_checks["min_confirmations"] is False
