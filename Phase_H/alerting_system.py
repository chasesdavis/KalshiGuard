"""Phase H alerting orchestration and threshold checks."""
from __future__ import annotations

from dataclasses import dataclass

from Shared.alerting import AlertingSystem
from Shared.audit_logger import AuditLogger
from Shared.config import Config


@dataclass(frozen=True)
class DrawdownSnapshot:
    """Minimal drawdown metric used for alert triggers."""

    daily_loss: float
    weekly_loss: float
    buying_power: float


class PhaseHAlertingSystem:
    """Applies risk-first alert rules and dispatches notifications."""

    def __init__(self, audit_logger: AuditLogger) -> None:
        self.audit_logger = audit_logger
        self.alerting = AlertingSystem(audit_logger=audit_logger)

    def evaluate_drawdown(self, snapshot: DrawdownSnapshot) -> bool:
        """Alert when risk controls approach or breach configured limits."""

        reasons: list[str] = []
        if snapshot.daily_loss >= Config.DRAWDOWN_DAILY_LIMIT:
            reasons.append("daily_drawdown_limit")
        if snapshot.weekly_loss >= Config.DRAWDOWN_WEEKLY_LIMIT:
            reasons.append("weekly_drawdown_limit")
        if snapshot.buying_power <= Config.MIN_BUYING_POWER:
            reasons.append("buying_power_floor")

        if not reasons:
            return False

        body = (
            f"Drawdown guardrail triggered: {', '.join(reasons)} | "
            f"daily_loss={snapshot.daily_loss:.2f}, weekly_loss={snapshot.weekly_loss:.2f}, "
            f"buying_power={snapshot.buying_power:.2f}"
        )
        self.alerting.send_alert(title="KalshiGuard Risk Alert", body=body, severity="critical")
        self.audit_logger.log_event(
            component="phase_h",
            event_type="drawdown_alert",
            severity="critical",
            message="Risk threshold breach",
            payload={"reasons": reasons, "snapshot": snapshot.__dict__},
        )
        return True
