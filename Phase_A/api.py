"""KalshiGuard API — read-only data endpoints plus Phase B/C/D analysis and paper trading."""
from __future__ import annotations

import os
import sys

from flask import Flask, jsonify

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Phase_A.analysis import analyze_snapshot_with_context
from Phase_A.data_fetcher import fetch_markets, fetch_price_snapshots
from Phase_A.logger import init_db, log_signal
from Phase_C.risk_gateway import RiskGateway
from Phase_D.backtest_harness import BacktestHarness
from Phase_D.demo_connector import DemoKalshiConnector
from Shared.bankroll_tracker import BankrollTracker
from Shared.config import Config
from Shared.models import PriceSnapshot
from Shared.logging_utils import configure_logging

configure_logging()
app = Flask(__name__)
init_db()


@app.route("/status")
def status():
    return jsonify(
        {
            "status": "ONLINE",
            "phase": "D (Paper Trading simulation active; live execution disabled)",
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
            "risk_assessment": {
                "approved": result.risk_assessment.approved,
                "proposed_stake": result.risk_assessment.proposed_stake,
                "kelly_fraction": result.risk_assessment.kelly_fraction,
                "ruin_probability": result.risk_assessment.ruin_probability,
                "stress_passed": result.risk_assessment.stress_passed,
                "reasons": result.risk_assessment.fail_safe_reasons,
            },
            "paper_trade_proposal": result.paper_trade_proposal.__dict__,
            "action": "NO ACTION (Phase D paper simulation only — execution disabled)",
        }
    )


@app.route("/risk_assessment/<ticker>")
def risk_assessment(ticker: str):
    snapshots = {s.ticker: s for s in fetch_price_snapshots()}
    snap = snapshots.get(ticker)
    if not snap:
        return jsonify({"error": f"No data for ticker: {ticker}"}), 404

    analysis = analyze_snapshot_with_context(snap)
    return jsonify(analysis.risk_assessment.__dict__)


@app.route("/paper_trade_sim/<ticker>")
def paper_trade_sim(ticker: str):
    """Run a single-market paper simulation including risk/stress projections."""
    connector = DemoKalshiConnector()
    cred_status = connector.credentials_status()

    try:
        payload = connector.fetch_market_snapshot(ticker)
    except ValueError as exc:
        return jsonify({"error": str(exc), "demo_signup": "https://demo.kalshi.co/"}), 404

    snapshots = {s.ticker: s for s in fetch_price_snapshots()}
    snap = snapshots.get(ticker)
    if not snap:
        return jsonify({"error": f"No baseline snapshot for ticker: {ticker}"}), 404

    sim_snapshot = PriceSnapshot(
        ticker=snap.ticker,
        timestamp=snap.timestamp,
        yes_ask=payload["yes_ask"],
        no_ask=payload["no_ask"],
        yes_bid=payload["yes_bid"],
        no_bid=payload["no_bid"],
        volume=snap.volume,
        open_interest=snap.open_interest,
    )

    analysis = analyze_snapshot_with_context(sim_snapshot)
    risk = RiskGateway().assess_paper_simulation(
        bankroll_tracker=BankrollTracker(starting_bankroll=50.0),
        probability_yes=analysis.probability_estimate.ensemble_yes,
        entry_price_cents=analysis.paper_trade_proposal.entry_price_cents,
    )

    harness_summary = BacktestHarness().run(trades=100)
    return jsonify(
        {
            "ticker": ticker,
            "market_source": payload["source"],
            "demo_credentials": cred_status.__dict__,
            "demo_signup": "https://demo.kalshi.co/",
            "proposal": analysis.paper_trade_proposal.__dict__,
            "risk_assessment": risk.__dict__,
            "pnl_projection": {
                "average_pnl": risk.average_pnl,
                "ruin_probability": risk.ruin_probability,
            },
            "stress": {
                "stress_passed": risk.stress_passed,
                "fail_safe_reasons": risk.fail_safe_reasons,
            },
            "backtest_100_trade_summary": harness_summary.__dict__,
        }
    )


if __name__ == "__main__":
    print("🛡️  KalshiGuard API starting on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
