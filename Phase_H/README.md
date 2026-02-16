# Phase H — Deployment & Monitoring 🚀

**Status:** ✅ Implemented

Phase H hardens KalshiGuard for always-on operation while preserving strict risk controls.

## What is included

- **24/7 runtime hardening**
  - `Dockerfile`
  - `docker-compose.yml` with healthcheck
  - `Phase_H/supervisord.conf`
  - `scripts/healthcheck.py`
- **Structured audit trail (SQLite)**
  - `Shared/audit_logger.py`
  - Queryable via API `GET /logs`
- **Alerting fanout**
  - `Shared/alerting.py`
  - `Phase_H/alerting_system.py`
  - iMessage and optional Telegram delivery
- **Deployment management**
  - `Shared/deployment.py`
  - `Phase_H/deployment_manager.py`
- **API monitoring endpoints**
  - `GET /health`
  - `GET /logs`
- **Global API error handling**
  - Unhandled exception audit logging + critical alert dispatch

## Environment

Add these to `.env` for Phase H:

```bash
APP_ENV=development
AUDIT_DB_PATH=phase_h_audit.db
ALERT_CHANNELS=imessage,telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
HEALTH_ERROR_STREAK_RESTART=3
HEALTH_LOG_RETENTION_DAYS=30
```

## Run Locally

```bash
python Phase_A/api.py
curl http://localhost:5000/health
curl "http://localhost:5000/logs?limit=20"
```

## Run via Docker Compose

```bash
docker compose up --build
```

## Tests

```bash
./scripts/run-tests.sh
```

or

```bash
./venv/bin/python -m pytest Phase_A/tests Phase_B/tests Phase_C/tests Phase_D/tests Phase_E/tests Phase_F/tests Phase_H/tests -v
```

## Operational notes

- Alerts are risk-first: drawdown and buying-power breaches trigger critical alerts.
- iMessage alert path uses the same whitelist transport foundation as trade approval.
- Telegram is optional and only used when both token and chat id are configured.
- `/health` includes restart recommendation based on consecutive error streak.
