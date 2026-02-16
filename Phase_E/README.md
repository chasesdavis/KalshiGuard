# Phase E — Live Trading (Mandatory Human Approval) 💰

**Status:** ✅ Implemented

## Scope Delivered
- Kalshi live API connector with HMAC request signing for `/trade-api/v2`.
- Shared order execution façade with market/limit request support.
- iMessage approval service enforcing whitelist (`+17657921945`) and exact command format:
  - `APPROVE TRADE ID <PROPOSAL_ID>`
- Integrated proposal flow:
  1. Phase B analysis computes side/EV/confidence.
  2. Phase C risk gateway enforces bankroll/risk hard limits.
  3. Proposal is sent to whitelisted iMessage recipient.
  4. Execution endpoint checks approval and submits live order only after approval.

## Security and Risk Guards
- Environment-only credentials (`KALSHI_API_KEY`, `KALSHI_API_SECRET`).
- No automatic execution path exists without explicit approval message.
- Non-whitelisted messages are ignored.
- Trading freezes if effective bankroll < $40.
- Per-trade max risk remains capped at `$0.50`.
- Mandatory approval applies to **every trade**.

## API Endpoints
- `POST /propose_trade/<ticker>`: run analysis + risk checks + send approval message.
- `POST /execute_approved`: check/record inbound approval and execute if approved.

## Test Coverage
- Proposal-to-execution end-to-end flow with mocked executor.
- Non-whitelisted approval rejection.
- iMessage parser/whitelist checks.
