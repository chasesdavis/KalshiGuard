"""Phase C iMessage proposal formatter (logging-only stub)."""
from __future__ import annotations

from dataclasses import dataclass
import logging
import uuid
from typing import Any

from Phase_E.imessage_sender import IMessageSender
from Phase_C.risk_gateway import RiskAssessment
from Shared.config import Config

logger = logging.getLogger(__name__)


def format_trade_proposal(analysis_result: Any, risk_assessment: RiskAssessment) -> str:
    """Build a human-readable proposal payload for future iMessage approval flow."""

    signal = analysis_result.signal
    decision = analysis_result.edge_decision
    stress = risk_assessment.stress_test

    return (
        f"[PROPOSAL ONLY — NO SEND]\n"
        f"Ticker: {signal.ticker}\n"
        f"Side: {signal.side}\n"
        f"EV: {signal.ev_percent:.2f}% | Confidence: {signal.confidence:.4f}\n"
        f"Confirmations: {decision.confirmation_count} ({', '.join(decision.confirmations) or 'none'})\n"
        f"Risk: ${risk_assessment.sizing.recommended_risk:.2f} "
        f"(Kelly applied {risk_assessment.sizing.kelly_fraction_applied:.4f})\n"
        f"Stress (n={stress.simulations}): ruin_prob={stress.ruin_probability:.2%}, "
        f"P5=${stress.p5_terminal:.2f}, P50=${stress.p50_terminal:.2f}, P95=${stress.p95_terminal:.2f}\n"
        f"Fail-safe approved: {risk_assessment.fail_safe_report.approved}\n"
        f"Whitelisted approvers configured: {len(Config.IMESSAGE_WHITELIST)}\n"
        f"Blockers: {', '.join(risk_assessment.blockers) or 'none'}"
    )


def log_trade_proposal(analysis_result: Any, risk_assessment: RiskAssessment) -> str:
    """Log proposal only; sending is intentionally disabled until a later phase."""

    proposal = format_trade_proposal(analysis_result, risk_assessment)
    logger.info("iMessage proposal stub generated:\n%s", proposal)
    return proposal


@dataclass
class TradeProposal:
    proposal_id: str
    ticker: str
    side: str
    contracts: int
    max_risk: float
    status: str = "PENDING_APPROVAL"


class ProposalRegistry:
    """In-memory proposal registry used by approval-gated execution flow."""

    def __init__(self) -> None:
        self._proposals: dict[str, TradeProposal] = {}
        self.sender = IMessageSender()

    def create_and_send(self, signal: Any, snapshot: Any, risk: Any) -> TradeProposal:
        proposal_id = f"{signal.ticker}-{uuid.uuid4().hex[:8]}".upper()
        side = signal.side if signal.side in {"YES", "NO"} else ("YES" if snapshot.yes_ask <= snapshot.no_ask else "NO")
        proposal = TradeProposal(
            proposal_id=proposal_id,
            ticker=signal.ticker,
            side=side,
            contracts=max(int(getattr(risk, "contracts", 1)), 1),
            max_risk=float(getattr(risk, "max_risk", Config.MAX_TRADE_RISK)),
        )
        self._proposals[proposal_id] = proposal

        message = (
            f"KalshiGuard proposal\n"
            f"Ticker: {proposal.ticker}\n"
            f"Side: {proposal.side}\n"
            f"Contracts: {proposal.contracts}\n"
            f"APPROVE TRADE ID {proposal_id}"
        )
        self.sender.send_trade_proposal(Config.IMESSAGE_WHITELIST[0], message)
        return proposal

    def get(self, proposal_id: str) -> TradeProposal | None:
        return self._proposals.get(proposal_id)

    def mark(self, proposal_id: str, status: str) -> TradeProposal | None:
        proposal = self.get(proposal_id)
        if proposal:
            proposal.status = status
        return proposal


REGISTRY = ProposalRegistry()
