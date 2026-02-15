# Phase E — Live Trading (Human-Approved) 💰

**Status:** 🔜 Planned (unlocks after 2+ weeks of Phase D paper trading)

## What This Phase Will Do
- Place real orders on Kalshi — ONLY after explicit iMessage approval
- Every trade proposal sent to whitelisted number (+17657921945) with:
  - Full reasoning, EV estimate, risk assessment, data sources
  - Prefix: "[KalshiGuard | Balance: $XX.XX]"
- Wait for "APPROVE TRADE ID XYZ" before executing
- Mandatory human approval for ALL trades until portfolio >$200
- Liquidity exit check: can exit full position at ≤2¢ worse
- No trading if effective buying power < $40

## Depends On
- Phase D (paper trading must show consistent positive results)
- Kalshi API credentials (KALSHI_API_KEY, KALSHI_API_SECRET)

## Key Files (to be created)
- `executor.py` — Real order placement (Kalshi REST API)
- `imessage_proposer.py` — Trade proposal formatting + send
- `approval_listener.py` — Wait for explicit approval from whitelist
