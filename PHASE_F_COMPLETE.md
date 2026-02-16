# PHASE_F_COMPLETE.md

## Phase F Delivered: Learning & Self-Improvement

Phase F is now fully implemented with **offline retraining**, **governance self-review**, and **versioned rollback tooling**.

## Build Details

### New Components
- `Phase_F/model_retrainer.py`
  - Offline retrain pipeline from SQLite historical data.
  - Uses `Shared/model_trainer.py` for conservative ensemble weight updates.
  - Writes timestamped retrain artifacts to `Phase_F/artifacts/`.
- `Phase_F/governance_engine.py`
  - Weekly-style performance review from `trade_signals`.
  - Produces policy adjustments via `Shared/governance.py`.
- `Phase_F/version_rollback.py`
  - Version registry with git commit metadata.
  - Rollback simulation command generation.

### Shared Extensions
- `Shared/model_trainer.py`
  - Lightweight trainer (ridge regression + probability calibration).
- `Shared/governance.py`
  - Risk-first adjustment policy for Kelly scaling and threshold tightening.

### Integrations
- `Phase_B/probability_engine.py`
  - Added retrain hooks:
    - persisted weight loading
    - calibration bias/temperature
    - retrain status and apply methods
- `Phase_C/risk_gateway.py`
  - Added governance-aware `run_self_review()`.
  - Kelly multiplier now scaled by governance outcome.
- `Phase_A/api.py`
  - Added `GET /retrain_models` and `GET /self_review`.

## How to Run

```bash
pip install -r requirements.txt
python -m pytest
python Phase_A/api.py
```

Then call:

```bash
curl http://localhost:5000/retrain_models
curl http://localhost:5000/self_review
```

## Weekly Review Simulation

1. Ensure `trade_signals` table has logged rows (call `/explain_trade/<ticker>` several times).
2. Run `/self_review`.
3. Inspect returned `adjustment.kelly_scale_factor` and rationale.
4. Optionally run `/retrain_models` to update probability weights.
5. Validate registered version in `Phase_F/artifacts/model_registry.json`.

## Validation Scope
- Retraining behavior (sample ingestion and artifact output).
- Governance edge cases (drawdown-triggered de-risking).
- Rollback simulation coverage.
- API endpoint coverage for new Phase F routes.

## Next Recommendations (Phase G)
1. Build SwiftUI dashboard for bankroll, drawdown, and recommendation feed.
2. Add WidgetKit glance view for risk mode + latest proposal confidence.
3. Expose read-only authenticated mobile endpoints (status, risk, retrain report).
4. Keep live execution disabled in app until governance and approval rails are complete.
