# Phase B — Analysis Engine 🧠

**Status:** 🔜 Planned (unlocks after Phase A validated)

## What This Phase Will Do
- Connect to external data anchors (CME FedWatch, FRED, NOAA, polling aggregates)
- Build ensemble probability models (Bayesian + lightweight neural nets)
- Detect multi-layer edges: external calibration arb, internal mispricings, market making
- Require ≥4 independent confirmations before flagging an edge
- EV threshold: ≥40% after fees for directional trades

## Depends On
- Phase A (data collection layer must be validated and stable)
- Historical backfill ≥6 months of Kalshi data

## Key Files (to be created)
- `probability_engine.py` — Ensemble model inference
- `edge_detector.py` — Multi-layer edge confirmation
- `external_data.py` — CME, FRED, NOAA connectors
