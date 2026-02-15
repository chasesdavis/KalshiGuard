"""Basic smoke tests for Phase A API."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from Phase_A.api import app

def test_status():
    client = app.test_client()
    r = client.get("/status")
    assert r.status_code == 200
    data = r.get_json()
    assert data["phase"].startswith("A")
    assert data["live_trading"] is False

def test_markets():
    client = app.test_client()
    r = client.get("/markets")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)

def test_explain_trade():
    client = app.test_client()
    r = client.get("/explain_trade/FED-RATE-25MAR")
    assert r.status_code == 200
    data = r.get_json()
    assert data["side"] == "HOLD"
    assert "action" in data

def test_explain_trade_missing():
    client = app.test_client()
    r = client.get("/explain_trade/FAKE-TICKER")
    assert r.status_code == 404
