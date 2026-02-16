"""KalshiGuard API — analysis, proposal, and approval-gated execution endpoints."""
from __future__ import annotations

import os
import sys

from flask import Flask, jsonify, request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Phase_A.analysis import analyze_snapshot_with_context, propose_trade_with_context
from Phase_A.data_fetcher import fetch_markets, fetch_price_snapshots
from Phase_A.logger import init_db, log_signal
from Phase_C.imessage_proposal import REGISTRY
from Phase_E.order_executor import OrderExecutor, OrderRequest
from Shared.config import Config
from Shared.logging_utils import configure_logging

configure_logging()
app = Flask(__name__)
init_db()
ORDER_EXECUTOR = OrderExecutor()


@app.route("/status")
def status():
    return jsonify(
        {
            "status": "ONLINE",
            "phase": "E (Live trading integrated; mandatory iMessage approval)",
            "bankroll": Config.BANKROLL_START,
            "max_risk_per_trade": Config.MAX_TRADE_RISK,
            "live_trading": True,
            "approval_required": True,
            "min_ev_threshold": Config.MIN_EV_THRESHOLD,
            "min_confirmations": Config.MIN_CONFIRMATIONS,
        }
    )


@app.route("/markets")
def markets():
    mkt_list = fetch_markets()
    return jsonify([m.__dict__ for m in mkt_list])


@app.route("/explain_trade/<ticker>")
def explain_trade(ticker: str):
    """Structured explanation for a potential trade in read-only mode."""
    snapshots = {s.ticker: s for s in fetch_price_snapshots()}
    snap = snapshots.get(ticker)
    if not snap:
        return jsonify({"error": f"No data for ticker: {ticker}"}), 404

    result = analyze_snapshot_with_context(snap)
    signal = result.signal
    log_signal(signal)

    return jsonify(
        {
            "ticker": signal.ticker,
            "side": signal.side,
            "ev_percent": signal.ev_percent,
            "confidence": signal.confidence,
            "explanation": signal.explanation,
            "data_sources": signal.data_sources,
            "probability_estimate": {
                "market_implied_yes": round(result.probability_estimate.market_implied_yes, 4),
                "external_yes": round(result.probability_estimate.external_yes, 4),
                "bayesian_yes": round(result.probability_estimate.bayesian_yes, 4),
                "internal_yes": round(result.probability_estimate.internal_yes, 4),
                "ensemble_yes": round(result.probability_estimate.ensemble_yes, 4),
            },
            "confirmations": result.edge_decision.confirmations,
            "confirmation_count": result.edge_decision.confirmation_count,
            "risk_checks": result.edge_decision.threshold_checks,
            "action": "PROPOSAL ONLY (execution requires iMessage approval)",
        }
    )


@app.route("/propose_trade/<ticker>", methods=["POST"])
def propose_trade(ticker: str):
    snapshots = {s.ticker: s for s in fetch_price_snapshots()}
    snap = snapshots.get(ticker)
    if not snap:
        return jsonify({"error": f"No data for ticker: {ticker}"}), 404

    proposal_result = propose_trade_with_context(snap)
    if not proposal_result.risk.approved:
        return jsonify(
            {
                "status": "REJECTED_BY_RISK",
                "ticker": ticker,
                "reason": proposal_result.risk.reason,
                "max_contracts": proposal_result.risk.max_contracts,
            }
        ), 400

    proposal = proposal_result.proposal
    return jsonify(
        {
            "status": proposal.status,
            "proposal_id": proposal.proposal_id,
            "ticker": proposal.ticker,
            "side": proposal.side,
            "contracts": proposal.contracts,
            "max_risk_dollars": proposal.max_risk_dollars,
            "approval_required_from": Config.IMESSAGE_WHITELIST[0],
        }
    )


@app.route("/execute_approved", methods=["POST"])
def execute_approved():
    payload = request.get_json(silent=True) or {}
    proposal_id = (payload.get("proposal_id") or "").upper()
    from_number = payload.get("from_number")
    incoming_message = payload.get("message")

    if not proposal_id:
        return jsonify({"error": "proposal_id is required"}), 400

    proposal = REGISTRY.get(proposal_id)
    if not proposal:
        return jsonify({"error": f"Unknown proposal_id: {proposal_id}"}), 404

    if from_number and incoming_message:
        REGISTRY.sender.record_incoming_message(from_number=from_number, body=incoming_message)

    approved = REGISTRY.sender.wait_for_trade_approval(proposal_id, timeout_seconds=3, poll_interval_seconds=0.1)
    if not approved:
        return jsonify({"status": "WAITING_FOR_APPROVAL", "proposal_id": proposal_id}), 202

    side = "yes" if proposal.side == "YES" else "no"
    request_obj = OrderRequest(
        ticker=proposal.ticker,
        side=side,
        contracts=proposal.contracts,
        order_type="market",
        client_order_id=proposal_id,
    )
    order_result = ORDER_EXECUTOR.place_order(request_obj)
    REGISTRY.mark(proposal_id, "EXECUTED")
    return jsonify(
        {
            "status": "EXECUTED",
            "proposal_id": proposal_id,
            "order_status": order_result.status,
            "order_id": order_result.order_id,
        }
    )


if __name__ == "__main__":
    print("🛡️  KalshiGuard API starting on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
