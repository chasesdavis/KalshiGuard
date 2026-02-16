from pathlib import Path

from Phase_B.probability_engine import ProbabilityEngine
from Phase_C.risk_gateway import RiskGateway
from Phase_F.governance_engine import GovernanceEngine
from Phase_F.model_retrainer import PhaseFModelRetrainer
from Phase_F.version_rollback import VersionRollbackManager
from Shared.bankroll_tracker import BankrollTracker
from Shared.governance import PerformanceSnapshot, GovernancePolicy


def test_probability_engine_retrain_hooks(tmp_path: Path):
    weights_path = tmp_path / "weights.json"
    engine = ProbabilityEngine(weights_path=weights_path)
    engine.apply_retrained_weights(
        weights={
            "market_implied_yes": 0.4,
            "external_yes": 0.3,
            "bayesian_yes": 0.2,
            "internal_yes": 0.1,
        },
        calibration_bias=0.01,
        calibration_temperature=1.05,
        metadata={"sample_count": 12},
    )

    reloaded = ProbabilityEngine(weights_path=weights_path)
    status = reloaded.get_retrain_status()

    assert status["weights"]["market_implied_yes"] == 0.4
    assert status["calibration_bias"] == 0.01
    assert status["metadata"]["sample_count"] == 12


def test_governance_policy_drawdown_tightens_risk():
    policy = GovernancePolicy()
    adjustment = policy.evaluate(
        PerformanceSnapshot(
            trade_count=30,
            wins=12,
            losses=18,
            total_pnl=-1.2,
            max_drawdown=2.3,
            daily_loss=0.22,
            weekly_loss=0.9,
        )
    )
    assert adjustment.kelly_scale_factor < 1.0
    assert adjustment.risk_mode == "capital_preservation"
    assert adjustment.min_ev_delta > 0


def test_risk_gateway_self_review_applies_scale(tmp_path: Path):
    db_path = tmp_path / "signals.db"
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE trade_signals (id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT, side TEXT, confidence REAL, ev_percent REAL)"
    )
    conn.executemany(
        "INSERT INTO trade_signals (ticker, side, confidence, ev_percent) VALUES (?, ?, ?, ?)",
        [("A", "YES", 0.98, -15.0) for _ in range(25)],
    )
    conn.commit()
    conn.close()

    tracker = BankrollTracker(daily_loss=0.24, weekly_loss=0.85)
    gateway = RiskGateway(tracker=tracker)
    gateway.governance_engine = GovernanceEngine(db_path=str(db_path))

    report = gateway.run_self_review()
    assert report.adjustment.kelly_scale_factor < 1.0


def test_version_rollback_simulation(tmp_path: Path):
    registry_path = tmp_path / "registry.json"
    manager = VersionRollbackManager(registry_path=registry_path)
    record = manager.register_version("Phase_F/artifacts/probability_weights.json", "test")

    plan = manager.simulate_rollback(record.version_id)
    assert plan["status"] == "simulation_only"
    assert "git checkout" in plan["git_command"]


def test_model_retrainer_runs_with_empty_db(tmp_path: Path):
    db_path = tmp_path / "empty.db"
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE price_snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, ticker TEXT, timestamp TEXT, yes_bid REAL, yes_ask REAL, no_bid REAL, no_ask REAL, volume INTEGER, open_interest INTEGER)"
    )
    conn.commit()
    conn.close()

    retrainer = PhaseFModelRetrainer(
        db_path=str(db_path),
        weights_path=tmp_path / "weights.json",
        artifacts_dir=tmp_path / "artifacts",
    )
    report = retrainer.retrain()

    assert report.sample_count == 0
    assert Path(report.artifact_path).exists()
