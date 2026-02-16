"""Phase E end-to-end tests with mocked execution transport."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from Phase_A.api import app
from Phase_C.imessage_proposal import REGISTRY
from Phase_C.risk_gateway import RiskDecision, RiskGateway
from Shared.config import Config


def _force_risk_approval(monkeypatch):
    monkeypatch.setattr(Config, "MIN_CONFIDENCE", 0.0)
    monkeypatch.setattr(Config, "MIN_EV_THRESHOLD", -100.0)
    monkeypatch.setattr(
        RiskGateway,
        "assess",
        lambda self, signal, snapshot, bankroll=Config.BANKROLL_START: RiskDecision(True, "Pass", 1, 0.5),
    )


def test_propose_trade_and_execute_after_whitelisted_approval(monkeypatch):
    client = app.test_client()
    _force_risk_approval(monkeypatch)

    proposal_response = client.post("/propose_trade/FED-RATE-25MAR")
    assert proposal_response.status_code == 200
    payload = proposal_response.get_json()
    assert payload["status"] == "PENDING_APPROVAL"
    proposal_id = payload["proposal_id"]
    assert REGISTRY.get(proposal_id) is not None

    from Phase_A import api as api_module

    class FakeOrderExecutor:
        def place_order(self, request_obj):
            return type("Result", (), {"status": "accepted", "order_id": "ord-123"})()

    monkeypatch.setattr(api_module, "ORDER_EXECUTOR", FakeOrderExecutor())

    execute_response = client.post(
        "/execute_approved",
        json={
            "proposal_id": proposal_id,
            "from_number": "+17657921945",
            "message": f"APPROVE TRADE ID {proposal_id}",
        },
    )
    assert execute_response.status_code == 200
    exec_payload = execute_response.get_json()
    assert exec_payload["status"] == "EXECUTED"
    assert exec_payload["order_id"] == "ord-123"


def test_non_whitelist_message_does_not_approve(monkeypatch):
    client = app.test_client()
    _force_risk_approval(monkeypatch)

    proposal_response = client.post("/propose_trade/FED-RATE-25MAR")
    proposal_id = proposal_response.get_json()["proposal_id"]

    from Phase_A import api as api_module

    class FakeOrderExecutor:
        def place_order(self, request_obj):
            raise AssertionError("Order should not execute without whitelisted approval")

    monkeypatch.setattr(api_module, "ORDER_EXECUTOR", FakeOrderExecutor())

    execute_response = client.post(
        "/execute_approved",
        json={
            "proposal_id": proposal_id,
            "from_number": "+15555550123",
            "message": f"APPROVE TRADE ID {proposal_id}",
        },
    )
    assert execute_response.status_code == 202
    payload = execute_response.get_json()
    assert payload["status"] == "WAITING_FOR_APPROVAL"
