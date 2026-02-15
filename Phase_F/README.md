# Phase F — Learning & Self-Improvement 🧬

**Status:** 🔜 Planned (unlocks after Phase E live track record)

## What This Phase Will Do
- Offline model retraining on accumulated trade data
- Weekly backtest of new strategy ideas
- Versioned model governance: every update tested + approved before deployment
- Rollback capability to last-known-good model
- Optional Codex Cloud integration for code optimization
- Retrain cadence: weekly (configurable)

## Depends On
- Phase E (live trade data needed for meaningful retraining)
- Sufficient historical data (≥3 months of live signals)

## Key Files (to be created)
- `trainer.py` — Offline model retraining pipeline
- `model_registry.py` — Versioned model storage + rollback
- `governance.py` — Approval workflow for model updates
