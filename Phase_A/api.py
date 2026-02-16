"""KalshiGuard API — data endpoints, analysis explanation, risk assessment, and Phase F learning hooks."""
from __future__ import annotations

import os
import sys

from flask import Flask, jsonify

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Phase_A.analysis import analyze_snapshot_with_context
from Phase_A.data_fetcher import fetch_markets, fetch_price_snapshots
from Phase_A.logger import init_db, log_signal
from Phase_F.model_retrainer import PhaseFModelRetrainer
from Phase_F.version_rollback import VersionRollbackManager
from Shared.config import Config
from Shared.logging_utils import configure_logging

configure_logging()
app = Flask(__name__)
init_db()

MODEL_RETRAINER = PhaseFModelRetrainer()
ROLLBACK_MANAGER = VersionRollbackManager()


@app.route("/status")
def status():
    return jsonify(
        {
            "status": "ONLINE",
            "phase": "F (Learning & Self-Improvement active; execution controls unchanged)",
            "bankroll": Config.BANKROLL_START,
            "max_risk_per_trade": Config.MAX_TRADE_RISK,
            "max_total_exposure": Config.MAX_TOTAL_EXPOSURE,
            "live_trading": False,
            "min_ev_threshold": Config.MIN_EV_THRESHOLD,
            "min_confirmations": Config.MIN_CONFIRMATIONS,
            "stress_simulations": Config.MONTE_CARLO_SIMS,
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
            "risk_assessment": _serialize_risk(result.risk_assessment),
            "proposal_preview": result.proposal_preview,
            "action": "NO ACTION (Phase F learning active; live execution controls unchanged)",
        }
    )


@app.route("/risk_assessment/<ticker>")
def risk_assessment(ticker: str):
    """Return Phase C pre-trade risk output for one ticker."""
    snapshots = {s.ticker: s for s in fetch_price_snapshots()}
    snap = snapshots.get(ticker)
    if not snap:
        return jsonify({"error": f"No data for ticker: {ticker}"}), 404

    result = analyze_snapshot_with_context(snap)
    return jsonify({"ticker": ticker, "risk_assessment": _serialize_risk(result.risk_assessment), "read_only": True})


@app.route("/retrain_models")
def retrain_models():
    """Trigger offline Phase F retraining and version registration."""
    report = MODEL_RETRAINER.retrain()
    version = ROLLBACK_MANAGER.register_version(
        artifact_path=report.weights_path,
        notes=f"sample_count={report.sample_count}; brier {report.old_brier}->{report.new_brier}",
    )
    return jsonify(
        {
            "status": report.status,
            "sample_count": report.sample_count,
            "old_brier": report.old_brier,
            "new_brier": report.new_brier,
            "artifact_path": report.artifact_path,
            "weights_path": report.weights_path,
            "codex_summary": report.codex_summary,
            "registered_version": version.__dict__,
        }
    )


@app.route("/self_review")
def self_review():
    """Run governance policy review and apply risk parameter adjustments."""
    # Run against singleton engine used by API compatibility layer.
    from Phase_A.analysis import _ENGINE

    applied = _ENGINE.risk_gateway.run_self_review()

    return jsonify(
        {
            "trade_count": applied.trade_count,
            "wins": applied.wins,
            "losses": applied.losses,
            "total_pnl": applied.total_pnl,
            "max_drawdown": applied.max_drawdown,
            "adjustment": {
                "kelly_scale_factor": applied.adjustment.kelly_scale_factor,
                "min_confidence_delta": applied.adjustment.min_confidence_delta,
                "min_ev_delta": applied.adjustment.min_ev_delta,
                "risk_mode": applied.adjustment.risk_mode,
                "rationale": applied.adjustment.rationale,
            },
        }
    )


def _serialize_risk(risk) -> dict:
    return {
        "approved": risk.approved,
        "blockers": risk.blockers,
        "bankroll": risk.bankroll,
        "buying_power": risk.buying_power,
        "sizing": {
            "recommended_risk": risk.sizing.recommended_risk,
            "kelly_fraction_raw": risk.sizing.kelly_fraction_raw,
            "kelly_fraction_applied": risk.sizing.kelly_fraction_applied,
            "max_risk_cap": risk.sizing.max_risk_cap,
            "exposure_cap_remaining": risk.sizing.exposure_cap_remaining,
            "rationale": risk.sizing.rationale,
        },
        "fail_safes": {
            "approved": risk.fail_safe_report.approved,
            "checks": risk.fail_safe_report.checks,
            "reasons": risk.fail_safe_report.reasons,
        },
        "stress_test": {
            "simulations": risk.stress_test.simulations,
            "steps": risk.stress_test.steps,
            "ruin_probability": risk.stress_test.ruin_probability,
            "p5_terminal": risk.stress_test.p5_terminal,
            "p50_terminal": risk.stress_test.p50_terminal,
            "p95_terminal": risk.stress_test.p95_terminal,
            "pass_threshold": risk.stress_test.pass_threshold,
        },
    }


if __name__ == "__main__":
    print("🛡️  KalshiGuard API starting on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
