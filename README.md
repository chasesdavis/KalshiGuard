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
| `Phase_D/` | **Paper Trading** — Simulated execution, backtesting harness (≥100 trades before live) | 🔜 Stub |
| `Phase_E/` | **Live Trading** — Human-approved order execution via iMessage (mandatory until $200+) | 🔜 Stub |
| `Phase_F/` | **Learning & Self-Improvement** — Offline model retraining, governance, versioned rollback | ✅ Implemented (offline) |
| `Phase_G/` | **iOS Companion App** — SwiftUI dashboard, WidgetKit, live PnL, glassmorphism UI | ✅ Implemented |
| `Phase_H/` | **Deployment & Monitoring** — Production hardening, 24/7 ops, alerting, audit logs | 🔜 Stub |
| `Shared/` | **Common utilities** — Models, config, Codex client, env loading | ✅ Scaffolded |
| `scripts/` | **Helpers** — Setup, Flask launcher, dashboard check, merge-conflict helper | ✅ Scaffolded |

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
| `IOS_DASHBOARD_TOKEN` | Phase G | Token auth between iOS dashboard/widget and Flask API |

## Rules (Non-Negotiable)

1. **Capital preservation > profit.** Every cent of the $50 is sacred.
2. **No live trades without iMessage approval** from whitelisted number.
3. **No secrets in code.** Environment variables only.
4. **Read-only first.** Each phase unlocks incrementally after validation.

## Conflict Resolution Helper (PR sync)

If PR branches are behind `main` and GitHub shows merge conflicts, run:

```bash
./scripts/resolve-pr-conflicts.sh <branch-1> <branch-2>
```

For a single branch, the original helper still works:

```bash
./scripts/resolve-pr3-conflicts.sh <your-branch>
```

The helper fetches `origin`, merges `origin/main` into each provided branch, runs tests, and pushes when conflict-free. If conflicts occur, it prints the exact next commands to finish manually.
