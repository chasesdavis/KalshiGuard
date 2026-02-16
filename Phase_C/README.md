# Phase C — Risk Management 🔒

**Status:** ✅ Implemented (read-only risk gating active)

## What This Phase Does
- Fractional Kelly micro-sizing with dynamic multiplier:
  - `0.10x` until bankroll reaches +20% growth
  - `0.25x` after +20% growth unlock
- Hard caps enforced:
  - `<= $0.50` risk per trade
  - `<= $2.00` total open exposure
  - no proposals if buying power falls below `$40`
- Pre-trade gauntlet:
  - Monte Carlo stress test with `1000` simulations
  - ruin threshold aligned to `$40` buying-power floor
  - strict gate on ruin probability
- Fail-safes:
  - drawdown checks (daily/weekly)
  - liquidity checks (volume + spread)
  - auto-veto on any failed check
- iMessage proposal stub:
  - formats full proposal payload with EV + risk context
  - logs only; no sending/execution logic

## Key Files
- `kelly_sizing.py` — conservative micro-position sizing
- `fail_safes.py` — veto rules for drawdown/liquidity/buying power
- `monte_carlo_stress.py` — 1000-run stress testing report
- `risk_gateway.py` — orchestrates sizing + fail-safe + stress
- `imessage_proposal.py` — logging-only proposal formatter

## Integration Points
- `Phase_B/analysis_engine.py` now appends risk details to explanations.
- `Phase_A/api.py` exposes `/risk_assessment/<ticker>` and includes `risk_assessment` in `/explain_trade/<ticker>`.

## Test Coverage
- Unit coverage for sizing, fail-safe rejection, Monte Carlo reporting.
- Integration test for Phase B engine embedding Phase C risk payload.
- API tests covering new risk endpoint.
