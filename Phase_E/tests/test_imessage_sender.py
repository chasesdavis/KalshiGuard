"""Unit tests for whitelist and approval parsing behavior."""
from Phase_E.imessage_sender import IMessageSender


def test_sender_enforces_whitelist():
    sender = IMessageSender()
    sender.send_trade_proposal("+17657921945", "hello")
    assert len(sender.outbox) == 1


def test_wait_for_approval_exact_trade_id():
    sender = IMessageSender()
    sender.record_incoming_message("+17657921945", "APPROVE TRADE ID ABC-123")
    assert sender.wait_for_trade_approval("ABC-123", timeout_seconds=1, poll_interval_seconds=0.01)
    assert not sender.wait_for_trade_approval("XYZ", timeout_seconds=0, poll_interval_seconds=0.01)
