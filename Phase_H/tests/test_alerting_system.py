from __future__ import annotations

from Phase_H.alerting_system import DrawdownSnapshot, PhaseHAlertingSystem
from Shared.audit_logger import AuditLogger


class _FakeSender:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    def send_trade_proposal(self, to_number: str, message: str):
        self.messages.append((to_number, message))
        return {"status": "queued"}


def test_drawdown_alert_triggered(monkeypatch, tmp_path):
    logger = AuditLogger(tmp_path / "audit.db")
    system = PhaseHAlertingSystem(audit_logger=logger)
    fake_sender = _FakeSender()
    monkeypatch.setattr(system.alerting, "sender", fake_sender)

    triggered = system.evaluate_drawdown(
        DrawdownSnapshot(daily_loss=0.3, weekly_loss=0.0, buying_power=45.0)
    )

    assert triggered is True
    assert len(fake_sender.messages) == 1
    events = logger.query_events(limit=5, component="phase_h", severity="critical")
    assert len(events) >= 1


def test_drawdown_no_alert_when_safe(tmp_path):
    logger = AuditLogger(tmp_path / "audit.db")
    system = PhaseHAlertingSystem(audit_logger=logger)

    triggered = system.evaluate_drawdown(
        DrawdownSnapshot(daily_loss=0.05, weekly_loss=0.1, buying_power=49.0)
    )

    assert triggered is False
