"""KalshiGuard API — data endpoints, analysis explanation, risk assessment, and Phase F learning hooks."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Phase_A.analysis import analyze_snapshot_with_context, propose_trade_with_context
from Phase_A.data_fetcher import fetch_markets, fetch_price_snapshots
from Phase_A.logger import init_db, log_signal
from Phase_C.imessage_proposal import REGISTRY
from Phase_D.backtest_harness import BacktestHarness
from Phase_F.model_retrainer import PhaseFModelRetrainer
from Phase_F.version_rollback import VersionRollbackManager
from Phase_H.alerting_system import DrawdownSnapshot, PhaseHAlertingSystem
from Phase_H.audit_logger import get_audit_logger
from Phase_H.deployment_manager import PhaseHDeploymentManager
from Shared.config import Config
from Shared.logging_utils import configure_logging
from Shared.order_executor import OrderExecutor, OrderRequest

configure_logging()
app = Flask(__name__)
init_db()
ORDER_EXECUTOR = OrderExecutor()

MODEL_RETRAINER = PhaseFModelRetrainer()
ROLLBACK_MANAGER = VersionRollbackManager()
AUDIT_LOGGER = get_audit_logger()
PHASE_H_DEPLOYMENT = PhaseHDeploymentManager(repo_root=Path(__file__).resolve().parent.parent, audit_logger=AUDIT_LOGGER)
PHASE_H_ALERTING = PhaseHAlertingSystem(audit_logger=AUDIT_LOGGER)
PHASE_H_DEPLOYMENT.ensure_assets()


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


@app.route("/health")
def health():
    """Production health snapshot for uptime monitors and orchestrators."""
    snapshot = PHASE_H_DEPLOYMENT.health_snapshot()
    AUDIT_LOGGER.log_event(
        component="api",
        event_type="health_check",
        severity="info",
        message="Health endpoint queried",
        payload={"uptime_seconds": snapshot.uptime_seconds, "error_streak": snapshot.error_streak},
    )
    return jsonify(
        {
            "status": "ok",
            "environment": Config.APP_ENV,
            "uptime_seconds": snapshot.uptime_seconds,
            "started_at": snapshot.app_started_at,
            "error_streak": snapshot.error_streak,
            "restart_recommended": snapshot.restart_recommended,
            "audit_db_path": Config.AUDIT_DB_PATH,
        }
    )


@app.route("/logs")
def logs():
    """Query structured audit logs."""
    limit = int(request.args.get("limit", "100"))
    component = request.args.get("component")
    severity = request.args.get("severity")
    since = request.args.get("since")
    events = AUDIT_LOGGER.query_events(limit=limit, component=component, severity=severity, since=since)
    return jsonify(
        {
            "count": len(events),
            "events": [event.__dict__ for event in events],
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
            "paper_trade_proposal": result.paper_trade_proposal.__dict__,
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


@app.route("/paper_trade_sim/<ticker>")
def paper_trade_sim(ticker: str):
    """Run a single proposal preview plus 100-trade deterministic backtest summary."""
    snapshots = {s.ticker: s for s in fetch_price_snapshots()}
    snap = snapshots.get(ticker)
    if not snap:
        return jsonify({"error": f"No data for ticker: {ticker}"}), 404

    result = analyze_snapshot_with_context(snap)
    backtest = BacktestHarness().run(trades=100)
    return jsonify(
        {
            "ticker": ticker,
            "proposal": result.paper_trade_proposal.__dict__,
            "backtest_100_trade_summary": backtest.__dict__,
            "read_only": True,
        }
    )


@app.route("/ios/dashboard")
def ios_dashboard():
    """Token-protected mobile dashboard payload for the Phase G iOS app/widget."""
    token_error = _require_ios_token()
    if token_error:
        return token_error

    snapshots = fetch_price_snapshots()
    tracked = snapshots[:5]
    now = datetime.now(timezone.utc)

    positions = []
    total_exposure = 0.0
    total_unrealized = 0.0
    for snap in tracked:
        avg_price = (snap.yes_ask + snap.yes_bid) / 2
        quantity = 1
        exposure = round(avg_price * quantity, 2)
        mark = round(snap.yes_bid, 2)
        unrealized = round((mark - avg_price) * quantity, 2)
        total_exposure += exposure
        total_unrealized += unrealized
        positions.append(
            {
                "ticker": snap.ticker,
                "side": "YES",
                "contracts": quantity,
                "avg_price": round(avg_price, 2),
                "mark_price": mark,
                "unrealized_pnl": unrealized,
                "confidence": 0.0,
            }
        )

    portfolio_value = round(Config.BANKROLL_START + total_unrealized, 2)
    history = _build_history_curve(base_value=Config.BANKROLL_START, points=24)

    return jsonify(
        {
            "status": "ONLINE",
            "last_updated": now.isoformat(),
            "phase": "G-companion-read-only",
            "portfolio": {
                "bankroll_start": Config.BANKROLL_START,
                "portfolio_value": portfolio_value,
                "daily_pnl": round(total_unrealized, 2),
                "daily_pnl_percent": round((total_unrealized / Config.BANKROLL_START) * 100, 2),
                "total_exposure": round(total_exposure, 2),
                "buying_power": round(max(0.0, Config.BANKROLL_START - total_exposure), 2),
                "live_trading": False,
            },
            "positions": positions,
            "history": history,
        }
    )


@app.route("/execute_approved", methods=["POST"])
def execute_approved():
    """Execute only after approval.

    Supports both:
    - Legacy Phase G stub payload (`approval_id`, `approved`)
    - Phase E approval-gated payload (`proposal_id`)
    """
    body = request.get_json(silent=True) or {}

    legacy_mode = ("approval_id" in body) or ("approved" in body)
    if legacy_mode:
        token_error = _require_ios_token()
        if token_error:
            return token_error

        approval_id = body.get("approval_id", "")
        approved = bool(body.get("approved", False))
        if not approved:
            return (
                jsonify(
                    {
                        "status": "DECLINED",
                        "message": "No execution attempted (approval flag false).",
                        "read_only": True,
                    }
                ),
                400,
            )
        return jsonify(
            {
                "status": "STUBBED",
                "approval_id": approval_id,
                "message": "Approval acknowledged by API stub. Live order execution remains disabled in this workspace.",
                "read_only": True,
                "executed": False,
            }
        )

    if "from_number" in body or "message" in body:
        return jsonify({"error": "Inbound approval message fields are not accepted on this endpoint."}), 400

    proposal_id = str(body.get("proposal_id", "")).strip().upper()
    if not proposal_id:
        return jsonify({"error": "proposal_id is required"}), 400

    proposal = REGISTRY.get(proposal_id)
    if proposal is None:
        return jsonify({"error": "Unknown proposal_id"}), 404
    if proposal.status != "PENDING_APPROVAL":
        payload = {"status": proposal.status, "proposal_id": proposal_id}
        if proposal.status == "EXECUTED":
            payload["error"] = "Proposal already executed"
        return jsonify(payload), 409

    approved = REGISTRY.sender.wait_for_trade_approval(proposal_id)
    if not approved:
        return jsonify({"status": "WAITING_FOR_APPROVAL", "proposal_id": proposal_id}), 202

    request_obj = OrderRequest(
        ticker=proposal.ticker,
        side="yes" if proposal.side == "YES" else "no",
        contracts=proposal.contracts,
        order_type="market",
        client_order_id=proposal.proposal_id,
    )
    result = ORDER_EXECUTOR.place_order(request_obj)
    REGISTRY.mark(proposal_id, "EXECUTED")
    AUDIT_LOGGER.log_event(
        component="api",
        event_type="order_executed",
        severity="info",
        message=f"Executed approved proposal {proposal_id}",
        payload={"proposal_id": proposal_id, "order_id": result.order_id, "order_status": result.status},
    )

    return jsonify(
        {
            "status": "EXECUTED",
            "proposal_id": proposal_id,
            "order_id": result.order_id,
            "order_status": result.status,
        }
    )


@app.route("/propose_trade/<ticker>", methods=["POST"])
def propose_trade(ticker: str):
    snapshots = {s.ticker: s for s in fetch_price_snapshots()}
    snap = snapshots.get(ticker)
    if not snap:
        return jsonify({"error": f"No data for ticker: {ticker}"}), 404

    result = propose_trade_with_context(snap)
    if result.proposal is None:
        AUDIT_LOGGER.log_event(
            component="api",
            event_type="proposal_rejected",
            severity="warning",
            message=f"Proposal rejected by risk for {ticker}",
            payload={"ticker": ticker, "reason": result.risk.reason},
        )
        return jsonify({"status": "REJECTED_BY_RISK", "reason": result.risk.reason}), 200

    AUDIT_LOGGER.log_event(
        component="api",
        event_type="proposal_created",
        severity="info",
        message=f"Proposal created for {ticker}",
        payload={
            "proposal_id": result.proposal.proposal_id,
            "ticker": result.proposal.ticker,
            "side": result.proposal.side,
            "contracts": result.proposal.contracts,
        },
    )
    return jsonify(
        {
            "status": "PENDING_APPROVAL",
            "proposal_id": result.proposal.proposal_id,
            "ticker": result.proposal.ticker,
            "side": result.proposal.side,
            "contracts": result.proposal.contracts,
        }
    )


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
    PHASE_H_ALERTING.evaluate_drawdown(
        DrawdownSnapshot(
            daily_loss=_ENGINE.risk_gateway.tracker.daily_loss,
            weekly_loss=_ENGINE.risk_gateway.tracker.weekly_loss,
            buying_power=_ENGINE.risk_gateway.tracker.buying_power,
        )
    )

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


def _build_history_curve(base_value: float, points: int) -> list[dict]:
    """Create deterministic synthetic equity points for dashboard charts."""
    start = datetime.now(timezone.utc) - timedelta(hours=points - 1)
    history = []
    for idx in range(points):
        timestamp = start + timedelta(hours=idx)
        drift = ((idx % 5) - 2) * 0.04
        value = round(base_value + (idx * 0.02) + drift, 2)
        history.append({"timestamp": timestamp.isoformat(), "value": value})
    return history


def _require_ios_token():
    """Validate dashboard token from Authorization, custom header, or query param."""
    expected = Config.IOS_DASHBOARD_TOKEN
    if not expected:
        return None

    auth_header = request.headers.get("Authorization", "")
    bearer_token = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else ""
    provided = bearer_token or request.headers.get("X-Dashboard-Token", "") or request.args.get("token", "")

    if provided != expected:
        return jsonify({"error": "Unauthorized dashboard token."}), 401
    return None


@app.errorhandler(Exception)
def handle_unhandled_exception(exc: Exception):
    """Global error handler with structured audit + alerting."""
    if isinstance(exc, HTTPException):
        return exc

    message = str(exc)
    PHASE_H_DEPLOYMENT.record_error(message)
    AUDIT_LOGGER.log_event(
        component="api",
        event_type="unhandled_exception",
        severity="critical",
        message=message,
        payload={"path": request.path, "method": request.method},
    )
    PHASE_H_ALERTING.alerting.send_alert(
        title="KalshiGuard API exception",
        body=f"{request.method} {request.path}: {message}",
        severity="critical",
    )
    return jsonify({"error": "internal_server_error", "message": "Unexpected server error."}), 500


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
