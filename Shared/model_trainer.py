"""Shared offline model-training utilities for Phase F.

The trainer is intentionally lightweight so it can run in constrained environments.
It focuses on calibration updates and ensemble re-weighting rather than complex
high-variance modeling. Capital preservation is prioritized over aggressiveness.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import numpy as np


@dataclass(frozen=True)
class TrainingSample:
    """Single training sample from historical market state and resolved outcome."""

    market_implied_yes: float
    external_yes: float
    bayesian_yes: float
    internal_yes: float
    outcome_yes: int


@dataclass(frozen=True)
class TrainingResult:
    """Model update payload from offline training."""

    sample_count: int
    old_brier: float
    new_brier: float
    weights: dict[str, float]
    calibration_bias: float
    calibration_temperature: float
    notes: str


class LightweightModelTrainer:
    """Retrains conservative ensemble parameters using least-squares + calibration."""

    feature_names = ("market_implied_yes", "external_yes", "bayesian_yes", "internal_yes")

    def train(self, samples: list[TrainingSample], baseline_weights: dict[str, float]) -> TrainingResult:
        if not samples:
            return TrainingResult(
                sample_count=0,
                old_brier=0.25,
                new_brier=0.25,
                weights=baseline_weights,
                calibration_bias=0.0,
                calibration_temperature=1.0,
                notes="No samples available; kept baseline weights.",
            )

        x = np.array([[getattr(s, name) for name in self.feature_names] for s in samples], dtype=float)
        y = np.array([s.outcome_yes for s in samples], dtype=float)

        baseline_vector = np.array([baseline_weights.get(name, 0.25) for name in self.feature_names], dtype=float)
        baseline_vector = self._normalize_nonnegative(baseline_vector)
        baseline_pred = np.clip(x @ baseline_vector, 0.01, 0.99)

        # Ridge-regularized least squares for stability.
        reg = 0.15
        ridge_matrix = reg * np.eye(x.shape[1])
        coeffs = np.linalg.pinv((x.T @ x) + ridge_matrix) @ (x.T @ y)
        coeffs = self._normalize_nonnegative(coeffs)

        raw_pred = np.clip(x @ coeffs, 0.01, 0.99)
        calibration_bias = float(np.clip(np.mean(y - raw_pred), -0.10, 0.10))
        calibrated_pred = np.clip(raw_pred + calibration_bias, 0.01, 0.99)

        # Temperature proxy: dampen variance when predictions are too sharp.
        variance = float(np.var(calibrated_pred))
        temperature = float(np.clip(1.0 + (0.05 - variance), 0.90, 1.20))
        adjusted_pred = np.clip((calibrated_pred - 0.5) / temperature + 0.5, 0.01, 0.99)

        old_brier = float(np.mean((baseline_pred - y) ** 2))
        new_brier = float(np.mean((adjusted_pred - y) ** 2))

        learned_weights = {name: round(float(value), 6) for name, value in zip(self.feature_names, coeffs)}

        return TrainingResult(
            sample_count=len(samples),
            old_brier=round(old_brier, 6),
            new_brier=round(new_brier, 6),
            weights=learned_weights,
            calibration_bias=round(calibration_bias, 6),
            calibration_temperature=round(temperature, 6),
            notes="Brier score improved" if new_brier <= old_brier else "No improvement; review needed",
        )

    @staticmethod
    def _normalize_nonnegative(vector: np.ndarray) -> np.ndarray:
        vector = np.clip(vector, 0.0, None)
        total = float(np.sum(vector))
        if total <= 0:
            return np.array([0.25, 0.25, 0.25, 0.25], dtype=float)
        return vector / total


def write_training_artifact(path: str | Path, result: TrainingResult) -> None:
    """Persist training result as a JSON artifact."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result.__dict__, indent=2), encoding="utf-8")
