"""Phase F offline model retraining pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from Phase_A.logger import DB_PATH
from Phase_B.probability_engine import ProbabilityEngine
from Shared.codex_client import get_codex_client
from Shared.model_trainer import LightweightModelTrainer, TrainingSample, TrainingResult, write_training_artifact


@dataclass(frozen=True)
class RetrainReport:
    status: str
    sample_count: int
    old_brier: float
    new_brier: float
    artifact_path: str
    weights_path: str
    codex_summary: str


class PhaseFModelRetrainer:
    """Coordinates historical-data extraction and probability ensemble retraining."""

    def __init__(
        self,
        db_path: str = DB_PATH,
        weights_path: str | Path | None = None,
        artifacts_dir: str | Path | None = None,
    ) -> None:
        self.db_path = db_path
        self.trainer = LightweightModelTrainer()
        self.engine = ProbabilityEngine(weights_path=weights_path)
        self.codex_client = get_codex_client()
        default_artifacts_dir = Path(__file__).resolve().parent / "artifacts"
        self.artifacts_dir = Path(artifacts_dir) if artifacts_dir else default_artifacts_dir

    def retrain(self) -> RetrainReport:
        samples = self._load_samples()
        baseline = self.engine.get_retrain_status()["weights"]
        result = self.trainer.train(samples, baseline)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        artifact_path = self.artifacts_dir / f"retrain_{timestamp}.json"
        write_training_artifact(artifact_path, result)

        status = "updated" if result.new_brier <= result.old_brier else "review_required"

        if status == "updated":
            self.engine.apply_retrained_weights(
                weights=result.weights,
                calibration_bias=result.calibration_bias,
                calibration_temperature=result.calibration_temperature,
                metadata={
                    "sample_count": result.sample_count,
                    "old_brier": result.old_brier,
                    "new_brier": result.new_brier,
                    "timestamp": timestamp,
                },
            )

        codex_summary = self._codex_review(result)

        return RetrainReport(
            status=status,
            sample_count=result.sample_count,
            old_brier=result.old_brier,
            new_brier=result.new_brier,
            artifact_path=str(artifact_path),
            weights_path=str(self.engine.weights_path),
            codex_summary=codex_summary,
        )

    def _load_samples(self) -> list[TrainingSample]:
        """Build weakly-supervised training samples from historical snapshot evolution."""
        if not Path(self.db_path).exists():
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT ticker, yes_bid, yes_ask, no_bid, no_ask, volume
            FROM price_snapshots
            ORDER BY ticker, timestamp ASC
            """
        ).fetchall()
        conn.close()

        by_ticker: dict[str, list[sqlite3.Row]] = {}
        for row in rows:
            by_ticker.setdefault(row["ticker"], []).append(row)

        samples: list[TrainingSample] = []
        for ticker_rows in by_ticker.values():
            for idx in range(len(ticker_rows) - 1):
                cur = ticker_rows[idx]
                nxt = ticker_rows[idx + 1]
                market_yes = self._clamp(((cur["yes_bid"] + cur["yes_ask"]) / 2) / 100.0)
                external_yes = self._clamp(market_yes + self._volume_tilt(cur["volume"]))
                bayesian_yes = self._clamp((market_yes * 0.65) + (external_yes * 0.35))
                internal_yes = self._clamp(market_yes - ((cur["yes_ask"] - cur["yes_bid"]) / 1000.0))

                next_mid = self._clamp(((nxt["yes_bid"] + nxt["yes_ask"]) / 2) / 100.0)
                outcome_yes = 1 if next_mid >= market_yes else 0

                samples.append(
                    TrainingSample(
                        market_implied_yes=market_yes,
                        external_yes=external_yes,
                        bayesian_yes=bayesian_yes,
                        internal_yes=internal_yes,
                        outcome_yes=outcome_yes,
                    )
                )

        return samples

    @staticmethod
    def _volume_tilt(volume: int) -> float:
        return max(min((volume - 10_000) / 250_000, 0.04), -0.04)

    @staticmethod
    def _clamp(probability: float) -> float:
        return min(max(float(probability), 0.01), 0.99)

    def _codex_review(self, result: TrainingResult) -> str:
        prompt = (
            "KalshiGuard Phase F retraining summary: "
            + json.dumps(
                {
                    "sample_count": result.sample_count,
                    "old_brier": result.old_brier,
                    "new_brier": result.new_brier,
                    "weights": result.weights,
                    "calibration_bias": result.calibration_bias,
                    "calibration_temperature": result.calibration_temperature,
                }
            )
            + " Provide one short risk-focused recommendation."
        )
        response = self.codex_client.generate_text(prompt, temperature=0.1, max_tokens=120)
        return response.strip() if response else "Codex unavailable; manual governance review required."
