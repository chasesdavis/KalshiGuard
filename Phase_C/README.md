# Phase C — Risk Management 🔒

**Status:** 🔜 Planned (unlocks after Phase B validated)

## What This Phase Will Do
- Implement fractional Kelly sizing (0.1–0.25x)
- Hard caps: ≤$0.50 risk per trade, ≤$2 total exposure, ≤$5 per theme
- Dynamic scaling: only increase caps after +20% portfolio growth
- Pre-trade gauntlet: Monte Carlo stress test (1000 simulations per trade)
- Post-trade monitoring with automatic partial exits
- Auto-shutdown: drawdown >$0.25 daily or >$1 weekly → kill switch

## Depends On
- Phase B (analysis engine must produce calibrated signals)

## Key Files (to be created)
- `risk_gateway.py` — Pre-trade risk checks
- `position_sizer.py` — Kelly fraction calculator
- `monte_carlo.py` — Stress testing harness
- `kill_switch.py` — Emergency shutdown monitor (60-second heartbeat)
