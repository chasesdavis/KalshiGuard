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


def test_sender_uses_bluebubbles_openclaw_when_configured(monkeypatch):
    monkeypatch.setattr(Config, "BLUEBUBBLES_SERVER_URL", "https://bb.local")
    monkeypatch.setattr(Config, "OPENCLAW_API_KEY", "openclaw-token")
    monkeypatch.setattr(Config, "OPENCLAW_SEND_PATH", "/openclaw/imessage/send")

    class FakeResponse:
        content = b'{"status":"sent"}'

        def raise_for_status(self):
            return None

        def json(self):
            return {"status": "sent"}

    captured = {}

    def fake_post(url, json, headers, timeout):
        captured.update({"url": url, "json": json, "headers": headers, "timeout": timeout})
        return FakeResponse()

    monkeypatch.setattr("Phase_E.imessage_sender.requests.post", fake_post)

    sender = IMessageSender()
    result = sender.send_trade_proposal("+17657921945", "proposal")

    assert captured["url"] == "https://bb.local/openclaw/imessage/send"
    assert captured["json"]["recipient"] == "+17657921945"
    assert captured["json"]["service"] == "iMessage"
    assert captured["headers"]["Authorization"] == "Bearer openclaw-token"
    assert result["status"] == "sent"
    assert result["provider"] == "bluebubbles-openclaw"
