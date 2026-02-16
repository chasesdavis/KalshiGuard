from types import SimpleNamespace

from Phase_B.analysis_engine import PhaseBAnalysisEngine
from Shared.models import PriceSnapshot


def test_analysis_engine_uses_no_adjusted_probability_for_no_proposals(monkeypatch):
    engine = PhaseBAnalysisEngine()

    snapshot = PriceSnapshot(
        ticker="TEST-NO",
        timestamp="2026-02-15T12:00:00Z",
        yes_bid=85,
        yes_ask=86,
        no_bid=14,
        no_ask=15,
        volume=10000,
        open_interest=50000,
    )

    captured = {}

    def fake_assess_trade(self, bankroll_tracker, probability_yes, entry_price_cents, active_exposure=0.0, trials=1000):
        captured["probability_yes"] = probability_yes
        return SimpleNamespace(
            approved=True,
            proposed_stake=1.0,
            kelly_fraction=0.1,
            fail_safe_reasons=[],
            stress_passed=True,
            ruin_probability=0.01,
            average_pnl=0.1,
        )

    monkeypatch.setattr(
        engine.risk_gateway,
        "assess_trade",
        fake_assess_trade.__get__(engine.risk_gateway, type(engine.risk_gateway)),
    )

    result = engine.analyze_snapshot(snapshot)

    assert result.paper_trade_proposal.side == "NO"
    assert captured["probability_yes"] == (1 - result.probability_estimate.ensemble_yes)
