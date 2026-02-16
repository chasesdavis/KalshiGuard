from __future__ import annotations

from Shared.audit_logger import AuditLogger


def test_audit_logger_round_trip(tmp_path):
    logger = AuditLogger(tmp_path / "audit.db")
    event_id = logger.log_event(
        component="phase_h",
        event_type="heartbeat",
        severity="info",
        message="Heartbeat ok",
        payload={"uptime_seconds": 12},
        trace_id="trace-1",
    )
    assert event_id > 0

    events = logger.query_events(limit=5)
    assert len(events) == 1
    event = events[0]
    assert event.component == "phase_h"
    assert event.event_type == "heartbeat"
    assert event.payload["uptime_seconds"] == 12
    assert event.trace_id == "trace-1"


def test_audit_logger_filters(tmp_path):
    logger = AuditLogger(tmp_path / "audit.db")
    logger.log_event(component="api", event_type="health", severity="info", message="ok")
    logger.log_event(component="api", event_type="error", severity="critical", message="boom")

    critical = logger.query_events(limit=10, severity="critical")
    assert len(critical) == 1
    assert critical[0].event_type == "error"
