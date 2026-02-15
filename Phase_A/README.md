# Phase A — Data Collection 📊

**Status:** ✅ Active (read-only)

## What This Phase Does
- Pulls public Kalshi market data (mock data for now; swap to real API later)
- Stores snapshots in SQLite (`kalshi_data.db`)
- Exposes a Flask API with read-only endpoints
- Generates structured trade explanations via `/explain_trade/<ticker>`
- Polls every 15 minutes (configurable)

## Endpoints
| Route | Method | Description |
|-------|--------|-------------|
| `/status` | GET | Bot health + current phase |
| `/markets` | GET | List tracked markets |
| `/explain_trade/<ticker>` | GET | Full EV explanation for a market |

## What This Phase Does NOT Do
- ❌ Place orders
- ❌ Access Kalshi auth endpoints
- ❌ Send iMessages
- ❌ Train models

## Run
```bash
cd KalshiGuard
python Phase_A/api.py
```
