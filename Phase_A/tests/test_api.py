"""Basic smoke tests for KalshiGuard API."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from Phase_A.api import app


def test_status():
    client = app.test_client()
    response = client.get("/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data["phase"].startswith("C")
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
