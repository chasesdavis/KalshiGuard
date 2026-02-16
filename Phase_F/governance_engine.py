"""Phase F governance and self-review engine."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3

from Phase_A.logger import DB_PATH
from Shared.governance import GovernanceAdjustment, GovernancePolicy, PerformanceSnapshot


@dataclass(frozen=True)
class GovernanceReport:
    trade_count: int
    wins: int
    losses: int
    total_pnl: float
    max_drawdown: float
    adjustment: GovernanceAdjustment


class GovernanceEngine:
    """Runs weekly-style governance analysis on logged trade signals."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self.policy = GovernancePolicy()

    def run_self_review(self, *, daily_loss: float = 0.0, weekly_loss: float = 0.0) -> GovernanceReport:
        perf = self._build_performance_snapshot(daily_loss=daily_loss, weekly_loss=weekly_loss)
        adjustment = self.policy.evaluate(perf)
        return GovernanceReport(
            trade_count=perf.trade_count,
            wins=perf.wins,
            losses=perf.losses,
            total_pnl=perf.total_pnl,
            max_drawdown=perf.max_drawdown,
            adjustment=adjustment,
        )

    def _build_performance_snapshot(self, *, daily_loss: float, weekly_loss: float) -> PerformanceSnapshot:
        if not Path(self.db_path).exists():
            return PerformanceSnapshot(0, 0, 0, 0.0, 0.0, daily_loss, weekly_loss)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT ticker, side, confidence, ev_percent
            FROM trade_signals
            ORDER BY id ASC
            """
        ).fetchall()
        conn.close()

        equity = 0.0
        peak = 0.0
        max_drawdown = 0.0
        wins = 0
        losses = 0

        for row in rows:
            confidence = float(row["confidence"])
            ev_percent = float(row["ev_percent"])
            side = row["side"]
            if side == "HOLD":
                continue

            pnl = max(min((ev_percent / 100.0) * 0.5, 0.5), -0.5)
            pnl *= max(min(confidence, 1.0), 0.0)
            if pnl >= 0:
                wins += 1
            else:
                losses += 1

            equity += pnl
            peak = max(peak, equity)
            max_drawdown = max(max_drawdown, peak - equity)

        return PerformanceSnapshot(
            trade_count=wins + losses,
            wins=wins,
            losses=losses,
            total_pnl=round(equity, 4),
            max_drawdown=round(max_drawdown, 4),
            daily_loss=daily_loss,
            weekly_loss=weekly_loss,
        )
