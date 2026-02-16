# Phase E Complete — Live Trading with Mandatory iMessage Approval

## What was built

### 1) Live Kalshi execution plumbing
- Added `Phase_E/live_connector.py` with HMAC-SHA256 request signing and authenticated REST calls to:
  - `POST /portfolio/orders`
  - `DELETE /portfolio/orders/{order_id}`
- Added `Shared/order_executor.py` and `Phase_E/order_executor.py` for reusable order placement/cancellation.

### 2) Human approval workflow (always required)
- Added `Phase_E/imessage_sender.py`:
  - Enforces whitelist: `+17657921945` only.
  - Sends via Twilio Messages API when `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_FROM_NUMBER` are configured.
  - Falls back to queued local transport for dev/test.
  - Polls inbound messages for exact approval format:
    - `APPROVE TRADE ID <ID>`
  - Ignores non-whitelisted and malformed messages.
- Added `Phase_C/imessage_proposal.py`:
  - Creates proposal IDs.
  - Formats proposal messages.
  - Sends proposal via iMessage sender.
  - Stores proposal state in an in-memory registry.

### 3) Risk gateway integration before proposal
- Added `Phase_C/risk_gateway.py`:
  - Blocks `HOLD` signals.
  - Enforces EV/confidence thresholds.
  - Freezes trading below `$40` buying power.
  - Caps max risk per trade to configured `$0.50`.

### 4) Analysis and API integration
- Updated `Phase_B/analysis_engine.py`:
  - New `propose_trade(snapshot)` orchestration (analysis -> risk -> proposal send).
- Updated `Phase_A/analysis.py`:
  - Added `propose_trade_with_context(snapshot)`.
- Updated `Phase_A/api.py` with Phase E endpoints:
  - `POST /propose_trade/<ticker>`
  - `POST /execute_approved`
- Updated `/status` to report Phase E and mandatory approval.

### 5) Test suite additions
- Added `Phase_E/tests/test_approval_flow.py`:
  - End-to-end proposal -> whitelisted approval -> mocked execution.
  - Non-whitelisted approval rejection path.
- Added `Phase_E/tests/test_imessage_sender.py`:
  - Whitelist enforcement and approval parser behavior.
- Updated `Phase_A/tests/test_api.py` for Phase E status fields.

---

## How to run

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run API
```bash
python Phase_A/api.py
```

### Simulate approval flow manually
1. Propose:
```bash
curl -X POST http://localhost:5000/propose_trade/FED-RATE-25MAR
```
2. Execute after approval text:
```bash
curl -X POST http://localhost:5000/execute_approved \
  -H "Content-Type: application/json" \
  -d '{
    "proposal_id": "<PASTE_PROPOSAL_ID>",
    "from_number": "+17657921945",
    "message": "APPROVE TRADE ID <PASTE_PROPOSAL_ID>"
  }'
```

---

## Notes
- This implementation intentionally keeps inbound iMessage ingestion abstract (`record_incoming_message`) so production can bind a secure webhook/bridge transport.
- Approval wait timeout is configurable with `APPROVAL_WAIT_TIMEOUT_SECONDS`.
- No secrets are stored in code; all credentials come from environment variables.
- Approval is mandatory for all trades regardless of bankroll level.

## Recommended next phase (Phase F)
- Add offline outcome labeling and model drift monitoring.
- Version and compare strategy/risk profiles with rollback support.
- Introduce governance rules for model promotion (minimum sample size, Sharpe bounds, drawdown limits).
- Build an immutable audit ledger linking proposal IDs, approvals, execution responses, and realized outcomes.
