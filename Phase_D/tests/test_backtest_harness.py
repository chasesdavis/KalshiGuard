"""Phase D backtest coverage."""
from Phase_D.backtest_harness import BacktestHarness


def test_backtest_runs_minimum_100_trades():
    summary = BacktestHarness().run(trades=100)
    assert summary.total_trades_requested == 100
    assert summary.total_trades_executed == 100
    assert summary.final_bankroll >= 0
    assert summary.ruin_detected is False
