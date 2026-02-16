# Phase F — Learning & Self-Improvement 🧬

**Status:** ✅ Implemented (offline-only, risk-first)

## What Phase F Adds

Phase F introduces controlled, auditable learning that improves model calibration **without touching live execution logic**.

### 1) Offline Model Retraining
- `Phase_F/model_retrainer.py` reads historical `price_snapshots` from SQLite.
- Builds weakly supervised labels from next-snapshot movement.
- Calls `Shared/model_trainer.py` for lightweight retraining (ridge-regularized reweighting + conservative calibration).
- Stores JSON artifacts in `Phase_F/artifacts/` and updates `Phase_B` ensemble weights via retrain hooks.

### 2) Governance & Weekly Self-Review
- `Phase_F/governance_engine.py` computes rolling performance and max drawdown from `trade_signals`.
- `Shared/governance.py` turns performance into conservative parameter changes.
- `Phase_C/risk_gateway.py` applies the governance output as a Kelly scaling factor (`kelly_scale_factor`).

### 3) Versioned Rollback
- `Phase_F/version_rollback.py` tracks model versions with git commit metadata.
- Registry is stored at `Phase_F/artifacts/model_registry.json`.
- Includes rollback simulation output (dry-run git checkout command).

## API Endpoints
- `GET /retrain_models`: triggers retraining, returns metrics + registered version.
- `GET /self_review`: runs governance review, returns risk adjustments.

## Safety Constraints
- Offline only; no live order flow changes.
- Capital-preservation bias in training and governance tuning.
- All secrets remain env-based (`CODEX_API_KEY` only via `Shared/codex_client.py`).
