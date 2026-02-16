# Phase D — Paper Trading 📝

**Status:** ✅ Implemented

## Overview
Phase D enables full paper-trading execution in demo/read-only mode:

- Demo market connector with env-based auth stubs (`DEMO_KALSHI_API_KEY`, `DEMO_KALSHI_API_SECRET`)
- Single-trade simulator route via Flask (`/paper_trade_sim/<ticker>`)
- Risk-first paper order lifecycle (proposal → risk gate → simulated resolution)
- Deterministic backtest harness with 100+ simulated trades starting from $50 mock bankroll
- Integration with Phase B analysis outputs and Phase C risk controls

## Files
- `demo_connector.py` — Demo API fetcher with resilient local fallback
- `paper_trader.py` — iMessage proposal stub logging + simulated execution orchestration
- `backtest_harness.py` — 100-trade replay batch and aggregate metrics
- `tests/` — Phase D tests for harness and edge cases

## Run
```bash
python Phase_A/api.py
```
Then call:
```bash
curl http://localhost:5000/paper_trade_sim/FED-RATE-25MAR
```

## Test
```bash
pytest Phase_A/tests Phase_B/tests Phase_C/tests Phase_D/tests -q
```

## Security/Risk Rules
- No live execution calls are made.
- All trade actions are simulated only.
- Every simulation starts from a $50 bankroll context.
- Risk gateway blocks entries with non-zero ruin probability, drawdown limit hits, or cap breaches.
