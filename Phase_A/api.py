"""Phase A Flask API — read-only endpoints for data and trade explanations."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, jsonify
from Phase_A.data_fetcher import fetch_markets, fetch_price_snapshots
from Phase_A.analysis import compute_ev_for_signal
from Phase_A.logger import init_db, log_signal
from Shared.config import Config

app = Flask(__name__)
init_db()

@app.route("/status")
def status():
    return jsonify({
        "status": "ONLINE",
        "phase": "A (Data Collection — Read-Only)",
        "bankroll": Config.BANKROLL_START,
        "max_risk_per_trade": Config.MAX_TRADE_RISK,
        "live_trading": False,
    })

@app.route("/markets")
def markets():
    mkt_list = fetch_markets()
    return jsonify([m.__dict__ for m in mkt_list])

@app.route("/explain_trade/<ticker>")
def explain_trade(ticker):
    """
    Structured explanation for a potential trade.
    Returns: summary, EV, confidence, data sources, risk factors, verdict.
    """
    snapshots = {s.ticker: s for s in fetch_price_snapshots()}
    snap = snapshots.get(ticker)
    if not snap:
        return jsonify({"error": f"No data for ticker: {ticker}"}), 404

    signal = compute_ev_for_signal(ticker, snap)
    log_signal(signal)

    return jsonify({
        "ticker": signal.ticker,
        "side": signal.side,
        "ev_percent": signal.ev_percent,
        "confidence": signal.confidence,
        "explanation": signal.explanation,
        "data_sources": signal.data_sources,
        "risk_checks": {
            "min_ev_met": signal.ev_percent >= Config.MIN_EV_THRESHOLD * 100,
            "min_confidence_met": signal.confidence >= Config.MIN_CONFIDENCE,
            "max_risk_ok": True,
        },
        "action": "NO ACTION (Phase A — read-only)",
    })

if __name__ == "__main__":
    print("🛡️  KalshiGuard Phase A API starting on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
