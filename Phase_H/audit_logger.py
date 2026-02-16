"""Phase H audit logger accessors."""
from __future__ import annotations

from Shared.audit_logger import AuditLogger
from Shared.config import Config


def get_audit_logger() -> AuditLogger:
    """Return initialized shared audit logger for Phase H services."""
    return AuditLogger(Config.AUDIT_DB_PATH)
