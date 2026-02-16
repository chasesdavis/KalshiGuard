# KalshiGuard 🛡️

**Autonomous Kalshi micro-trading workspace — $50 bankroll, capital preservation first.**

Every live trade requires explicit human approval via iMessage.
Codex Cloud integration reads `CODEX_API_KEY` from environment — no secrets in code.

## Phase Folders

| Folder | Purpose | Status |
|--------|---------|--------|
| `Phase_A/` | **Data Collection** — Read-only Kalshi data fetcher, models, SQLite logging, Flask API, `/explain_trade` | ✅ Scaffolded |
| `Phase_B/` | **Analysis Engine** — EV calculation, edge detection, multi-source probability models | ✅ Implemented (read-only) |
| `Phase_C/` | **Risk Management** — Position sizing, fractional Kelly, Monte Carlo stress tests, fail-safes | ✅ Implemented (read-only) |
| `Phase_D/` | **Paper Trading** — Simulated execution, backtesting harness (≥100 trades before live) | ✅ Implemented |
| `Phase_E/` | **Live Trading** — Human-approved order execution via iMessage (mandatory until $200+) | ✅ Implemented |
| `Phase_F/` | **Learning & Self-Improvement** — Offline model retraining, governance, versioned rollback | ✅ Implemented (offline) |
| `Phase_G/` | **iOS Companion App** — SwiftUI dashboard, WidgetKit, live PnL, glassmorphism UI | ✅ Implemented |
| `Phase_H/` | **Deployment & Monitoring** — Production hardening, 24/7 ops, alerting, audit logs | ✅ Implemented |
| `Shared/` | **Common utilities** — Models, config, Codex client, env loading | ✅ Scaffolded |
| `scripts/` | **Helpers** — Setup, Flask launcher, dashboard check | ✅ Scaffolded |

## Quick Start

```bash
cd KalshiGuard
pip install -r requirements.txt
cp .env.example .env          # add your keys here (never commit .env)
python Phase_A/api.py         # start API on :5000 (Phase D paper simulation enabled)
# health check:                curl http://localhost:5000/health
```

## Environment Variables

| Var | Required | Purpose |
|-----|----------|---------|
| `CODEX_API_KEY` | Optional | Codex Cloud code-generation calls |
| `DEMO_KALSHI_API_KEY` | Optional (Phase D) | Demo Kalshi API key for paper simulations |
| `DEMO_KALSHI_API_SECRET` | Optional (Phase D) | Demo Kalshi API secret for paper simulations |
| `KALSHI_API_KEY` | Phase E+ | Kalshi API authentication |
| `KALSHI_API_SECRET` | Phase E+ | Kalshi API secret |
| `IOS_DASHBOARD_TOKEN` | Phase G | Token auth between iOS dashboard/widget and Flask API |
| `AUDIT_DB_PATH` | Phase H | SQLite path for structured audit events |
| `ALERT_CHANNELS` | Phase H | Alert fanout channels (`imessage,telegram`) |
| `TELEGRAM_BOT_TOKEN` | Optional (Phase H) | Telegram Bot API token for alerts |
| `TELEGRAM_CHAT_ID` | Optional (Phase H) | Telegram chat destination for alerts |
| `HEALTH_ERROR_STREAK_RESTART` | Phase H | Error streak threshold before restart recommendation |

## Rules (Non-Negotiable)

1. **Capital preservation > profit.** Every cent of the $50 is sacred.
2. **No live trades without iMessage approval** from whitelisted number (+17657921945) on every trade.
3. **No secrets in code.** Environment variables only.
4. **Read-only first.** Each phase unlocks incrementally after validation.
