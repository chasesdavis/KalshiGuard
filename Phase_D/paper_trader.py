"""Phase D paper trading orchestration."""
from __future__ import annotations

from dataclasses import dataclass

from Phase_B.analysis_engine import AnalysisResult
from Phase_C.imessage_proposal import IMessageProposal, log_proposal
from Phase_C.risk_gateway import RiskAssessment
from Shared.bankroll_tracker import BankrollTracker
from Shared.trade_simulator import SimulatedTrade, TradeSimulator


@dataclass(frozen=True)
class PaperTradeResult:
    ticker: str
    side: str
    approved: bool
    risk: RiskAssessment
    simulated_trade: SimulatedTrade | None
    bankroll_after: float


class PaperTrader:
    """Consumes analysis+risk outputs and runs simulated execution lifecycle."""

    def run_single_simulation(
        self,
        analysis: AnalysisResult,
        risk: RiskAssessment,
        bankroll_tracker: BankrollTracker,
    ) -> PaperTradeResult:
        proposal = IMessageProposal(
            ticker=analysis.signal.ticker,
            side=analysis.edge_decision.side,
            stake_dollars=risk.proposed_stake,
            rationale=analysis.signal.explanation.splitlines()[0],
        )
        log_proposal(proposal)

        simulated: SimulatedTrade | None = None
        if risk.approved and analysis.edge_decision.side in {"YES", "NO"}:
            entry = analysis.snapshot.yes_ask if analysis.edge_decision.side == "YES" else analysis.snapshot.no_ask
            simulated = TradeSimulator.simulate_resolution(
                ticker=analysis.signal.ticker,
                side=analysis.edge_decision.side,
                stake_dollars=risk.proposed_stake,
                entry_price_cents=entry,
                probability_yes=analysis.probability_estimate.ensemble_yes,
            )
            bankroll_tracker.apply_pnl(simulated.pnl_dollars)

        return PaperTradeResult(
            ticker=analysis.signal.ticker,
            side=analysis.edge_decision.side,
            approved=risk.approved,
            risk=risk,
            simulated_trade=simulated,
            bankroll_after=bankroll_tracker.current_bankroll,
        )
