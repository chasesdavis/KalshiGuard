"""Proposal management that bridges analysis/risk to iMessage approval and execution."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from Phase_C.risk_gateway import RiskDecision
from Phase_E.imessage_sender import IMessageSender
from Shared.config import Config
from Shared.models import EVSignal, PriceSnapshot


@dataclass(frozen=True)
class TradeProposal:
    proposal_id: str
    ticker: str
    side: str
    contracts: int
    max_risk_dollars: float
    status: str
    message: str


class ProposalRegistry:
    """In-memory proposal registry used by API execution endpoints."""

    def __init__(self) -> None:
        self._store: dict[str, TradeProposal] = {}
        self.sender = IMessageSender()

    def create_and_send(self, signal: EVSignal, snapshot: PriceSnapshot, risk: RiskDecision) -> TradeProposal:
        proposal_id = str(uuid.uuid4()).upper()
        msg = (
            f"[KalshiGuard | Balance: ${Config.BANKROLL_START:.2f}]\n"
            f"TRADE ID {proposal_id}\n"
            f"Ticker: {snapshot.ticker}\n"
            f"Side: {signal.side}\n"
            f"Contracts: {risk.max_contracts}\n"
            f"Risk: ${risk.estimated_risk_dollars:.2f}\n"
            f"EV: {signal.ev_percent:.2f}% | Confidence: {signal.confidence:.3f}\n"
            f"Reply exactly: APPROVE TRADE ID {proposal_id}"
        )
        self.sender.send_trade_proposal(Config.IMESSAGE_WHITELIST[0], msg)
        proposal = TradeProposal(
            proposal_id=proposal_id,
            ticker=snapshot.ticker,
            side=signal.side,
            contracts=risk.max_contracts,
            max_risk_dollars=risk.estimated_risk_dollars,
            status="PENDING_APPROVAL",
            message=msg,
        )
        self._store[proposal_id] = proposal
        return proposal

    def get(self, proposal_id: str) -> TradeProposal | None:
        return self._store.get(proposal_id)

    def mark(self, proposal_id: str, status: str) -> TradeProposal:
        proposal = self._store[proposal_id]
        updated = TradeProposal(**{**proposal.__dict__, "status": status})
        self._store[proposal_id] = updated
        return updated


REGISTRY = ProposalRegistry()
