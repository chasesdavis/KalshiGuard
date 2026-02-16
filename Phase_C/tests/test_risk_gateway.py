from Phase_B.analysis_engine import PhaseBAnalysisEngine
from Phase_C.fail_safes import FailSafeEvaluator
from Phase_C.kelly_sizing import FractionalKellySizer
from Phase_C.monte_carlo_stress import MonteCarloStressTester
from Shared.bankroll_tracker import BankrollTracker
from Shared.models import PriceSnapshot


def _snapshot() -> PriceSnapshot:
    return PriceSnapshot(
        ticker="FED-RATE-25MAR",
        timestamp="2026-02-15T12:00:00Z",
        yes_bid=72,
        yes_ask=74,
        no_bid=26,
        no_ask=28,
        volume=45000,
        open_interest=820000,
    )


def test_fractional_kelly_respects_hard_caps():
    sizer = FractionalKellySizer()
    decision = sizer.size_risk(
        side="YES",
        prob_yes=0.80,
        bankroll=50.0,
        kelly_multiplier=0.25,
        exposure_cap_remaining=2.0,
    )

    assert decision.recommended_risk <= 0.50
    assert decision.kelly_fraction_applied >= 0.0


def test_fail_safe_rejects_low_buying_power():
    report = FailSafeEvaluator().evaluate(
        snapshot=_snapshot(),
        buying_power=39.5,
        daily_loss=0.0,
        weekly_loss=0.0,
    )
    assert report.approved is False
    assert "buying_power_floor" in report.reasons


def test_stress_tester_returns_1000_simulations():
    report = MonteCarloStressTester().run(
        bankroll=50.0,
        risk_amount=0.5,
        win_probability=0.58,
        payout_multiple=0.35,
    )
    assert report.simulations == 1000
    assert 0.0 <= report.ruin_probability <= 1.0


def test_analysis_engine_embeds_risk_assessment():
    engine = PhaseBAnalysisEngine()
    result = engine.analyze_snapshot(_snapshot())
    assert result.risk_assessment.sizing.recommended_risk <= 0.5
    assert "Proposed risk" in result.signal.explanation
    assert "PROPOSAL ONLY" in result.proposal_preview


def test_bankroll_tracker_dynamic_scaling():
    tracker = BankrollTracker(realized_pnl=11.0)
    assert tracker.kelly_multiplier == 0.25
