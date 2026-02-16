from __future__ import annotations

from Phase_H.deployment_manager import PhaseHDeploymentManager
from Shared.audit_logger import AuditLogger
from Shared.deployment import DeploymentManager


def test_write_deployment_assets(tmp_path):
    logger = AuditLogger(tmp_path / "audit.db")
    manager = PhaseHDeploymentManager(repo_root=tmp_path, audit_logger=logger)

    written = manager.ensure_assets()
    assert "Dockerfile" in written
    assert "docker-compose.yml" in written
    assert "Phase_H/supervisord.conf" in written

    # Second run should be idempotent.
    assert manager.ensure_assets() == []


def test_restart_policy_threshold():
    assert DeploymentManager.should_restart(3) is True
    assert DeploymentManager.should_restart(0) is False
