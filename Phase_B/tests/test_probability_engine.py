from Phase_B.external_data import ExternalDataProvider
from Phase_B.probability_engine import ProbabilityEngine
from Shared.models import PriceSnapshot


def test_probability_estimate_ranges():
    provider = ExternalDataProvider()
    engine = ProbabilityEngine()
    snapshot = PriceSnapshot(
        ticker="FED-RATE-25MAR",
        timestamp="2026-02-15T12:00:00Z",
        yes_bid=72,
        yes_ask=74,
        no_bid=26,
        no_ask=28,
        volume=45000,
        open_interest=820000,
    )

    anchors = provider.get_probability_anchors(snapshot.ticker)
    estimate = engine.estimate_yes_probability(snapshot, anchors)
    confidence = engine.aggregate_confidence(estimate, anchors)

    assert 0.0 < estimate.ensemble_yes < 1.0
    assert 0.0 <= estimate.model_agreement <= 1.0
    assert 0.0 <= confidence <= 0.99
