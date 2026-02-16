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
    assert data["phase"].startswith("D")
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


def test_explain_trade_missing():
    client = app.test_client()
    response = client.get("/explain_trade/FAKE-TICKER")
    assert response.status_code == 404
