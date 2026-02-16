"""Basic smoke tests for KalshiGuard API."""
from types import SimpleNamespace

from Phase_B.analysis_engine import PaperTradeProposal
from Phase_C.risk_gateway import RiskAssessment
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from Phase_A import api
from Phase_A.api import app
from Phase_F.model_retrainer import PhaseFModelRetrainer
from Phase_F.version_rollback import VersionRollbackManager


def test_status():
    client = app.test_client()
    response = client.get("/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["phase"].startswith("F")
    assert data["live_trading"] is False


def test_markets():
    client = app.test_client()
    response = client.get("/markets")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_explain_trade():
    client = app.test_client()
    response = client.get("/explain_trade/FED-RATE-25MAR")
    assert response.status_code == 200
    data = response.get_json()
    assert data["side"] in {"HOLD", "YES", "NO"}
    assert "probability_estimate" in data
    assert "confirmations" in data
    assert "risk_assessment" in data
    assert "paper_trade_proposal" in data
    assert "action" in data


def test_paper_trade_sim():
    client = app.test_client()
    response = client.get("/paper_trade_sim/FED-RATE-25MAR")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ticker"] == "FED-RATE-25MAR"
    assert "backtest_100_trade_summary" in payload
    assert payload["proposal"]["generation_mode"] in {"edge_confirmed", "repricing_fallback"}


def test_explain_trade_missing():
    client = app.test_client()
    response = client.get("/explain_trade/FAKE-TICKER")
    assert response.status_code == 404


def test_risk_assessment():
    client = app.test_client()
    response = client.get("/risk_assessment/FED-RATE-25MAR")
    assert response.status_code == 200
    data = response.get_json()
    assert "risk_assessment" in data
    assert "stress_test" in data["risk_assessment"]


def test_retrain_models_endpoint(tmp_path):
    api.MODEL_RETRAINER = PhaseFModelRetrainer(
        db_path=str(tmp_path / "phase_f.db"),
        weights_path=tmp_path / "weights.json",
        artifacts_dir=tmp_path / "artifacts",
    )
    api.ROLLBACK_MANAGER = VersionRollbackManager(registry_path=tmp_path / "registry.json")

    client = app.test_client()
    response = client.get("/retrain_models")
    assert response.status_code == 200
    data = response.get_json()
    assert "status" in data
    assert "registered_version" in data


def test_self_review_endpoint():
    client = app.test_client()
    response = client.get("/self_review")
    assert response.status_code == 200
    data = response.get_json()
    assert "adjustment" in data
    assert "kelly_scale_factor" in data["adjustment"]


def test_ios_dashboard_without_token_when_unset():
    client = app.test_client()
    previous = api.Config.IOS_DASHBOARD_TOKEN
    api.Config.IOS_DASHBOARD_TOKEN = None
    try:
        response = client.get("/ios/dashboard")
        assert response.status_code == 200
        data = response.get_json()
        assert "portfolio" in data
        assert "positions" in data
    finally:
        api.Config.IOS_DASHBOARD_TOKEN = previous


def test_ios_dashboard_requires_token_when_set():
    client = app.test_client()
    previous = api.Config.IOS_DASHBOARD_TOKEN
    api.Config.IOS_DASHBOARD_TOKEN = "phase-g-token"
    try:
        unauthorized = client.get("/ios/dashboard")
        assert unauthorized.status_code == 401

        authorized = client.get("/ios/dashboard", headers={"Authorization": "Bearer phase-g-token"})
        assert authorized.status_code == 200
    finally:
        api.Config.IOS_DASHBOARD_TOKEN = previous


def test_execute_approved_stub_requires_approved_flag():
    client = app.test_client()
    previous = api.Config.IOS_DASHBOARD_TOKEN
    api.Config.IOS_DASHBOARD_TOKEN = "phase-g-token"
    try:
        declined = client.post(
            "/execute_approved",
            json={"approval_id": "abc", "approved": False},
            headers={"Authorization": "Bearer phase-g-token"},
        )
        assert declined.status_code == 400

        accepted = client.post(
            "/execute_approved",
            json={"approval_id": "abc", "approved": True},
            headers={"Authorization": "Bearer phase-g-token"},
        )
        assert accepted.status_code == 200
        assert accepted.get_json()["executed"] is False
    finally:
        api.Config.IOS_DASHBOARD_TOKEN = previous


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert "uptime_seconds" in payload
    assert "restart_recommended" in payload


def test_logs_endpoint_returns_audit_events():
    client = app.test_client()
    api.AUDIT_LOGGER.log_event(
        component="api",
        event_type="test_log",
        severity="info",
        message="log endpoint test",
        payload={"source": "test"},
    )
    response = client.get("/logs?limit=10&component=api")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["count"] >= 1
    assert isinstance(payload["events"], list)
