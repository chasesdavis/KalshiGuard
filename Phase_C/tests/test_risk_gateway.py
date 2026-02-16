"""Risk gateway tests for drawdown and stress behavior."""

from Phase_C.risk_gateway import RiskGateway
from Shared.bankroll_tracker import BankrollTracker


def test_risk_gateway_blocks_daily_drawdown():
    tracker = BankrollTracker(starting_bankroll=50.0)
    tracker.daily_pnl = -0.26
    assessment = RiskGateway().assess_trade(
        bankroll_tracker=tracker,
        probability_yes=0.7,
        entry_price_cents=60,
    )
    assert assessment.approved is False
    assert "daily_drawdown_limit_hit" in assessment.fail_safe_reasons
