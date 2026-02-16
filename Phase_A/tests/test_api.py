"""Basic smoke tests for KalshiGuard API."""
from types import SimpleNamespace

from Phase_B.analysis_engine import PaperTradeProposal
from Phase_C.risk_gateway import RiskAssessment
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
    assert payload["proposal"]["generation_mode"] in {"edge_confirmed", "repricing_fallback"}


def test_explain_trade_missing():
    client = app.test_client()
    response = client.get("/explain_trade/FAKE-TICKER")
    assert response.status_code == 404


def test_paper_trade_sim_allows_demo_only_ticker(monkeypatch):
    from Phase_A import api

    def fake_fetch_market_snapshot(self, ticker: str):
        return {
            "ticker": ticker,
            "yes_ask": 61.0,
            "no_ask": 39.0,
            "yes_bid": 60.0,
            "no_bid": 38.0,
            "volume": 1234,
            "open_interest": 5678,
            "source": "demo_api",
        }

    fake_analysis = SimpleNamespace(
        probability_estimate=SimpleNamespace(ensemble_yes=0.62),
        paper_trade_proposal=PaperTradeProposal(
            ticker="DEMO-ONLY",
            side="YES",
            entry_price_cents=61.0,
            probability_yes=0.62,
            approved_by_risk=True,
            proposed_stake=2.5,
            risk_reasons=[],
            generation_mode="edge_confirmed",
        ),
    )

    monkeypatch.setattr(api.DemoKalshiConnector, "fetch_market_snapshot", fake_fetch_market_snapshot)
    monkeypatch.setattr(api, "fetch_price_snapshots", lambda: [])
    monkeypatch.setattr(api, "analyze_snapshot_with_context", lambda snapshot: fake_analysis)
    monkeypatch.setattr(
        api.RiskGateway,
        "assess_paper_simulation",
        lambda self, bankroll_tracker, probability_yes, entry_price_cents: RiskAssessment(
            approved=True,
            proposed_stake=2.5,
            kelly_fraction=0.05,
            fail_safe_reasons=[],
            stress_passed=True,
            ruin_probability=0.01,
            average_pnl=0.2,
        ),
    )
    monkeypatch.setattr(api.BacktestHarness, "run", lambda self, trades=100: SimpleNamespace(trades_executed=trades))

    client = app.test_client()
    response = client.get("/paper_trade_sim/DEMO-ONLY")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ticker"] == "DEMO-ONLY"
    assert payload["market_source"] == "demo_api"
