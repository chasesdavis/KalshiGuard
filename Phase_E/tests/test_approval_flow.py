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
    monkeypatch.setattr(Config, "APPROVAL_WAIT_TIMEOUT_SECONDS", 1)
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

    REGISTRY.sender.record_incoming_message(
        from_number="+17657921945",
        body=f"APPROVE TRADE ID {proposal_id}",
    )
    execute_response = client.post("/execute_approved", json={"proposal_id": proposal_id})
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

    REGISTRY.sender.record_incoming_message(
        from_number="+15555550123",
        body=f"APPROVE TRADE ID {proposal_id}",
    )
    execute_response = client.post("/execute_approved", json={"proposal_id": proposal_id})
    assert execute_response.status_code == 202
    payload = execute_response.get_json()
    assert payload["status"] == "WAITING_FOR_APPROVAL"


def test_execute_approved_prevents_duplicate_orders(monkeypatch):
    client = app.test_client()
    _force_risk_approval(monkeypatch)

    proposal_response = client.post("/propose_trade/FED-RATE-25MAR")
    proposal_id = proposal_response.get_json()["proposal_id"]

    from Phase_A import api as api_module

    class FakeOrderExecutor:
        def __init__(self):
            self.calls = 0

        def place_order(self, request_obj):
            self.calls += 1
            return type("Result", (), {"status": "accepted", "order_id": "ord-123"})()

    executor = FakeOrderExecutor()
    monkeypatch.setattr(api_module, "ORDER_EXECUTOR", executor)

    REGISTRY.sender.record_incoming_message(
        from_number="+17657921945",
        body=f"APPROVE TRADE ID {proposal_id}",
    )
    first_response = client.post("/execute_approved", json={"proposal_id": proposal_id})
    assert first_response.status_code == 200

    second_response = client.post("/execute_approved", json={"proposal_id": proposal_id})
    assert second_response.status_code == 409
    second_payload = second_response.get_json()
    assert second_payload["error"] == "Proposal already executed"
    assert executor.calls == 1
