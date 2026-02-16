"""KalshiGuard API — read-only data endpoints plus Phase B analysis explanation."""
from __future__ import annotations

import os
import sys

from flask import Flask, jsonify

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Phase_A.analysis import analyze_snapshot_with_context
from Phase_A.data_fetcher import fetch_markets, fetch_price_snapshots
from Phase_A.logger import init_db, log_signal
from Shared.config import Config
from Shared.logging_utils import configure_logging

configure_logging()
app = Flask(__name__)
init_db()


@app.route("/status")
def status():
    return jsonify(
        {
            "status": "ONLINE",
            "phase": "B (Analysis Engine active; read-only execution)",
            "bankroll": Config.BANKROLL_START,
            "max_risk_per_trade": Config.MAX_TRADE_RISK,
            "live_trading": False,
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
            "action": "NO ACTION (Phase B analysis only — execution disabled)",
        }
    )


if __name__ == "__main__":
    print("🛡️  KalshiGuard API starting on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
