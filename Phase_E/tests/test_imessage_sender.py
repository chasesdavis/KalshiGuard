"""Unit tests for whitelist and approval parsing behavior."""
from __future__ import annotations

from Phase_E.imessage_sender import IMessageSender
from Shared.config import Config


def test_sender_enforces_whitelist():
    sender = IMessageSender()
    sender.send_trade_proposal("+17657921945", "hello")
    assert len(sender.outbox) == 1


def test_wait_for_approval_exact_trade_id():
    sender = IMessageSender()
    sender.record_incoming_message("+17657921945", "APPROVE TRADE ID ABC-123")
    assert sender.wait_for_trade_approval("ABC-123", timeout_seconds=1, poll_interval_seconds=0.01)
    assert not sender.wait_for_trade_approval("XYZ", timeout_seconds=0, poll_interval_seconds=0.01)


def test_sender_uses_twilio_when_credentials_present(monkeypatch):
    monkeypatch.setattr(Config, "TWILIO_ACCOUNT_SID", "AC123")
    monkeypatch.setattr(Config, "TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setattr(Config, "TWILIO_FROM_NUMBER", "+19990000000")

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"status": "sent"}

    captured = {}

    def fake_post(url, data, auth, timeout):
        captured.update({"url": url, "data": data, "auth": auth, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setattr("Phase_E.imessage_sender.requests.post", fake_post)

    sender = IMessageSender()
    result = sender.send_trade_proposal("+17657921945", "proposal")

    assert "Accounts/AC123/Messages.json" in captured["url"]
    assert captured["data"]["To"] == "+17657921945"
    assert captured["auth"] == ("AC123", "token")
    assert result["status"] == "sent"
