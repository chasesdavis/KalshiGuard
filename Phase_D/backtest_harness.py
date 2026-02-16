"""Backtest harness to execute >=100 paper trades under risk-first constraints."""
from __future__ import annotations

from dataclasses import dataclass

from Phase_A.data_fetcher import fetch_price_snapshots
from Phase_B.analysis_engine import PhaseBAnalysisEngine
from Phase_C.risk_gateway import RiskGateway
from Phase_D.paper_trader import PaperTradeResult, PaperTrader
from Shared.bankroll_tracker import BankrollTracker
from Shared.codex_client import get_codex_client
from Shared.models import PriceSnapshot


@dataclass(frozen=True)
class BacktestSummary:
    total_trades_requested: int
    total_trades_executed: int
    approved_trades: int
    final_bankroll: float
    total_pnl: float
    max_drawdown_pct: float
    ruin_detected: bool
    codex_notes: str | None


class BacktestHarness:
    """Runs deterministic replay-style paper-trade simulation batches."""

    def __init__(self) -> None:
        self.engine = PhaseBAnalysisEngine()
        self.risk = RiskGateway()
        self.trader = PaperTrader()

    def run(self, trades: int = 100) -> BacktestSummary:
        snapshots = fetch_price_snapshots()
        tracker = BankrollTracker(starting_bankroll=50.0)
        executed = 0
        approved = 0

        for idx in range(trades):
            snapshot = self._derive_snapshot(snapshots[idx % len(snapshots)], idx)
            analysis = self.engine.analyze_snapshot(snapshot)
            entry = analysis.paper_trade_proposal.entry_price_cents
            assessment = self.risk.assess_trade(
                bankroll_tracker=tracker,
                probability_yes=analysis.probability_estimate.ensemble_yes,
                entry_price_cents=entry,
                active_exposure=0.0,
            )
            result: PaperTradeResult = self.trader.run_single_simulation(
                analysis, assessment, tracker, log_i_message_stub=False
            )
            executed += 1
            approved += int(result.approved and result.simulated_trade is not None)

            if tracker.current_bankroll <= 0:
                break

        codex_notes = self._optional_codex_summary(executed, tracker)
        return BacktestSummary(
            total_trades_requested=trades,
            total_trades_executed=executed,
            approved_trades=approved,
            final_bankroll=round(tracker.current_bankroll, 4),
            total_pnl=round(tracker.current_bankroll - tracker.starting_bankroll, 4),
            max_drawdown_pct=tracker.max_drawdown_pct,
            ruin_detected=tracker.current_bankroll <= 0,
            codex_notes=codex_notes,
        )

    @staticmethod
    def _derive_snapshot(base: PriceSnapshot, idx: int) -> PriceSnapshot:
        """Create slight deterministic perturbations for replay diversity."""
        shift = (idx % 5) - 2
        yes_ask = min(99, max(1, base.yes_ask + shift))
        no_ask = min(99, max(1, 100 - yes_ask))
        return PriceSnapshot(
            ticker=base.ticker,
            timestamp=base.timestamp,
            yes_bid=max(1, yes_ask - 2),
            yes_ask=yes_ask,
            no_bid=max(1, no_ask - 2),
            no_ask=no_ask,
            volume=base.volume + (idx * 11),
            open_interest=base.open_interest,
        )

    @staticmethod
    def _optional_codex_summary(executed: int, tracker: BankrollTracker) -> str | None:
        client = get_codex_client()
        prompt = (
            "Summarize this paper trading run in one sentence with capital-preservation framing: "
            f"trades={executed}, final_bankroll={tracker.current_bankroll:.2f}, drawdown_pct={tracker.max_drawdown_pct:.2f}."
        )
        return client.generate_text(prompt, max_tokens=80) if client.is_available() else None
