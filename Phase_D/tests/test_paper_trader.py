"""Paper trade edge-case tests."""

from Phase_A.data_fetcher import fetch_price_snapshots
from Phase_B.analysis_engine import PhaseBAnalysisEngine
from Phase_C.risk_gateway import RiskGateway
from Phase_D.paper_trader import PaperTrader
from Shared.bankroll_tracker import BankrollTracker


def test_paper_trade_handles_rejected_risk():
    snapshot = fetch_price_snapshots()[0]
    analysis = PhaseBAnalysisEngine().analyze_snapshot(snapshot)

    tracker = BankrollTracker(starting_bankroll=50.0)
    tracker.daily_pnl = -0.30  # trigger drawdown gate
    risk = RiskGateway().assess_trade(
        bankroll_tracker=tracker,
        probability_yes=analysis.probability_estimate.ensemble_yes,
        entry_price_cents=snapshot.yes_ask,
    )

    result = PaperTrader().run_single_simulation(analysis, risk, tracker)
    assert risk.approved is False
    assert result.simulated_trade is None
    assert result.bankroll_after == 50.0
