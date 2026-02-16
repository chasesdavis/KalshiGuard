"""Phase H audit logging utilities.

Stores structured events in SQLite for durable system decision trails.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class AuditEvent:
    """Immutable view of one persisted audit event."""

    id: int
    timestamp: str
    component: str
    event_type: str
    severity: str
    message: str
    payload: dict[str, Any]
    trace_id: str | None


class AuditLogger:
    """SQLite-backed audit logger for monitoring and incident analysis."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS audit_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        component TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        trace_id TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp
                    ON audit_events(timestamp)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_audit_events_component_severity
                    ON audit_events(component, severity)
                    """
                )

    def log_event(
        self,
        *,
        component: str,
        event_type: str,
        severity: str,
        message: str,
        payload: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> int:
        """Persist one audit event and return inserted row id."""

        payload = payload or {}
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._lock:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO audit_events(
                        timestamp, component, event_type, severity, message, payload_json, trace_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        timestamp,
                        component,
                        event_type,
                        severity,
                        message,
                        json.dumps(payload, separators=(",", ":"), sort_keys=True),
                        trace_id,
                    ),
                )
                return int(cursor.lastrowid)

    def query_events(
        self,
        *,
        limit: int = 100,
        component: str | None = None,
        severity: str | None = None,
        since: str | None = None,
    ) -> list[AuditEvent]:
        """Query recent events with optional filters."""

        capped_limit = max(1, min(limit, 1000))
        clauses: list[str] = []
        params: list[Any] = []

        if component:
            clauses.append("component = ?")
            params.append(component)
        if severity:
            clauses.append("severity = ?")
            params.append(severity)
        if since:
            clauses.append("timestamp >= ?")
            params.append(since)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (
            "SELECT id, timestamp, component, event_type, severity, message, payload_json, trace_id "
            f"FROM audit_events {where_sql} ORDER BY id DESC LIMIT ?"
        )
        params.append(capped_limit)

        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(sql, params).fetchall()

        events: list[AuditEvent] = []
        for row in rows:
            events.append(
                AuditEvent(
                    id=int(row["id"]),
                    timestamp=str(row["timestamp"]),
                    component=str(row["component"]),
                    event_type=str(row["event_type"]),
                    severity=str(row["severity"]),
                    message=str(row["message"]),
                    payload=json.loads(row["payload_json"]),
                    trace_id=row["trace_id"],
                )
            )
        return events

    def purge_older_than(self, days: int) -> int:
        """Delete events older than retention window and return count."""

        cutoff = datetime.now(timezone.utc) - timedelta(days=max(days, 1))
        with self._lock:
            with self._connect() as conn:
                cursor = conn.execute("DELETE FROM audit_events WHERE timestamp < ?", (cutoff.isoformat(),))
                return int(cursor.rowcount)
