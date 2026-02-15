# Phase D — Paper Trading 📝

**Status:** 🔜 Planned (unlocks after Phase C validated)

## What This Phase Will Do
- Simulate trade execution against live Kalshi orderbooks (no real orders)
- Backtest ≥100 simulated trades with full EV/risk logging
- Track simulated P&L, Sharpe ratio, max drawdown
- Run for minimum 2 weeks before Phase E approval
- Generate daily reports with per-trade explanations

## Depends On
- Phase C (risk management must pass stress tests)

## Key Files (to be created)
- `paper_executor.py` — Simulated order execution
- `backtest_harness.py` — Historical replay engine
- `performance_tracker.py` — Sharpe, drawdown, P&L metrics
