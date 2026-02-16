# Phase B — Analysis Engine 🧠

**Status:** ✅ Implemented (read-only analysis, no execution)

## Implemented Components
- `external_data.py` — mock external calibration anchors (CME/FRED/NOAA style interfaces)
- `probability_engine.py` — market + external + Bayesian + internal ensemble probability model
- `edge_detector.py` — confirmation stack and EV/confirmation/confidence threshold gates
- `analysis_engine.py` — orchestration layer that produces structured analysis payloads
- `tests/` — unit tests for probability and edge decision behavior

## Key Risk Rules Enforced
- Minimum EV gate: **40%**
- Minimum confirmations: **4 independent confirmations**
- Minimum confidence: **97%**
- If any gate fails, output is forced to `HOLD`

## Notes
- Phase B remains read-only.
- No Kalshi auth is used.
- External connectors are currently deterministic stubs to keep CI stable.
