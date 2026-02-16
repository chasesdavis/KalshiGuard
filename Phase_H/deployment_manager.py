"""Phase H deployment manager and runtime health checks."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from Shared.audit_logger import AuditLogger
from Shared.config import Config
from Shared.deployment import DeploymentManager


@dataclass(frozen=True)
class HealthSnapshot:
    """Point-in-time runtime health state."""

    now: str
    app_started_at: str
    uptime_seconds: int
    last_error: str | None
    error_streak: int
    restart_recommended: bool


class PhaseHDeploymentManager:
    """Coordinates deployment asset generation and runtime restart policy."""

    def __init__(self, repo_root: str | Path, audit_logger: AuditLogger) -> None:
        self.repo_root = Path(repo_root)
        self.audit_logger = audit_logger
        self.deployment = DeploymentManager(self.repo_root)
        self.app_started_at = datetime.now(timezone.utc)
        self.last_error: str | None = None
        self.error_streak = 0

    def ensure_assets(self) -> list[str]:
        """Write deployment assets if missing."""

        written = self.deployment.write_assets(overwrite=False, use_codex=True)
        self.audit_logger.log_event(
            component="phase_h",
            event_type="deployment_assets_sync",
            severity="info",
            message="Deployment assets synchronized",
            payload={"written": written},
        )
        return written

    def record_error(self, message: str) -> None:
        """Track app error streak for restart recommendation logic."""

        self.last_error = message
        self.error_streak += 1

    def record_success(self) -> None:
        """Reset streak after successful heartbeat cycle."""

        self.error_streak = 0
        self.last_error = None

    def health_snapshot(self) -> HealthSnapshot:
        """Generate restart-policy-aware health snapshot."""

        now = datetime.now(timezone.utc)
        uptime_seconds = int((now - self.app_started_at).total_seconds())
        restart_recommended = self.error_streak >= Config.HEALTH_ERROR_STREAK_RESTART
        return HealthSnapshot(
            now=now.isoformat(),
            app_started_at=self.app_started_at.isoformat(),
            uptime_seconds=uptime_seconds,
            last_error=self.last_error,
            error_streak=self.error_streak,
            restart_recommended=restart_recommended,
        )
