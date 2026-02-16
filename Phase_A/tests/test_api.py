"""Basic smoke tests for KalshiGuard API."""
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
    assert "action" in data


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
