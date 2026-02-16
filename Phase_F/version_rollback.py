"""Versioned rollback helpers for Phase F strategy/model artifacts."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess


@dataclass(frozen=True)
class VersionRecord:
    version_id: str
    git_commit: str
    artifact_path: str
    created_at: str
    notes: str


class VersionRollbackManager:
    """Tracks model versions with git commit context and supports rollback simulation."""

    def __init__(self, registry_path: str | Path | None = None) -> None:
        default_path = Path(__file__).resolve().parent / "artifacts" / "model_registry.json"
        self.registry_path = Path(registry_path) if registry_path else default_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

    def register_version(self, artifact_path: str, notes: str) -> VersionRecord:
        history = self._load_registry()
        version_id = f"v{len(history) + 1:04d}"
        record = VersionRecord(
            version_id=version_id,
            git_commit=self._current_commit(),
            artifact_path=artifact_path,
            created_at=datetime.now(timezone.utc).isoformat(),
            notes=notes,
        )
        history.append(record.__dict__)
        self._write_registry(history)
        return record

    def latest_version(self) -> VersionRecord | None:
        history = self._load_registry()
        if not history:
            return None
        return VersionRecord(**history[-1])

    def simulate_rollback(self, target_version_id: str) -> dict[str, str]:
        """Return a dry-run rollback plan without mutating git state."""
        history = self._load_registry()
        match = next((r for r in history if r["version_id"] == target_version_id), None)
        if not match:
            raise ValueError(f"Unknown version id: {target_version_id}")

        return {
            "target_version": target_version_id,
            "target_commit": match["git_commit"],
            "artifact_path": match["artifact_path"],
            "git_command": f"git checkout {match['git_commit']} -- {match['artifact_path']}",
            "status": "simulation_only",
        }

    def _load_registry(self) -> list[dict]:
        if not self.registry_path.exists():
            return []
        return json.loads(self.registry_path.read_text(encoding="utf-8"))

    def _write_registry(self, history: list[dict]) -> None:
        self.registry_path.write_text(json.dumps(history, indent=2), encoding="utf-8")

    @staticmethod
    def _current_commit() -> str:
        try:
            return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        except Exception:
            return "unknown"
