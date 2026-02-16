# KalshiGuard 🛡️

**Autonomous Kalshi micro-trading workspace — $50 bankroll, capital preservation first.**

Every live trade requires explicit human approval via iMessage.
Codex Cloud integration reads `CODEX_API_KEY` from environment — no secrets in code.

## Phase Folders

| Folder | Purpose | Status |
|--------|---------|--------|
| `Phase_A/` | **Data Collection** — Read-only Kalshi data fetcher, models, SQLite logging, Flask API, `/explain_trade` | ✅ Scaffolded |
| `Phase_B/` | **Analysis Engine** — EV calculation, edge detection, multi-source probability models | ✅ Implemented (read-only) |
| `Phase_C/` | **Risk Management** — Position sizing, fractional Kelly, Monte Carlo stress tests, fail-safes | 🔜 Stub |
| `Phase_D/` | **Paper Trading** — Simulated execution, backtesting harness (≥100 trades before live) | 🔜 Stub |
| `Phase_E/` | **Live Trading** — Human-approved order execution via iMessage (mandatory for every trade) | ✅ Implemented |
| `Phase_F/` | **Learning & Self-Improvement** — Offline model retraining, governance, versioned rollback | 🔜 Stub |
| `Phase_G/` | **iOS Companion App** — SwiftUI dashboard, WidgetKit, live PnL, glassmorphism UI | 🔜 Stub |
| `Phase_H/` | **Deployment & Monitoring** — Production hardening, 24/7 ops, alerting, audit logs | 🔜 Stub |
| `Shared/` | **Common utilities** — Models, config, Codex client, env loading | ✅ Scaffolded |
| `scripts/` | **Helpers** — Setup, Flask launcher, dashboard check | ✅ Scaffolded |

## Quick Start

```bash
cd KalshiGuard
pip install -r requirements.txt
cp .env.example .env          # add your keys here (never commit .env)
python Phase_A/api.py         # start read-only API on :5000 (Phase B analysis enabled)
```

## Environment Variables

| Var | Required | Purpose |
|-----|----------|---------|
| `CODEX_API_KEY` | Optional | Codex Cloud code-generation calls |
| `KALSHI_API_KEY` | Phase E+ | Kalshi API authentication |
| `KALSHI_API_SECRET` | Phase E+ | Kalshi API secret |
| `TWILIO_ACCOUNT_SID` | Optional | Twilio outbound proposal delivery |
| `TWILIO_AUTH_TOKEN` | Optional | Twilio auth token |
| `TWILIO_FROM_NUMBER` | Optional | Twilio sender phone number |
| `APPROVAL_WAIT_TIMEOUT_SECONDS` | Optional | Wait timeout for approval polling (default 60) |

## Rules (Non-Negotiable)

1. **Capital preservation > profit.** Every cent of the $50 is sacred.
2. **No live trades without iMessage approval** from whitelisted number (+17657921945) on every trade.
3. **No secrets in code.** Environment variables only.
4. **Read-only first.** Each phase unlocks incrementally after validation.
