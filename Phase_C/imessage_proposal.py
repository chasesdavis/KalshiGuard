"""iMessage proposal stub for mandatory human-approval workflow.

Phase D only logs proposal payloads; no outbound messages are sent.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IMessageProposal:
    ticker: str
    side: str
    stake_dollars: float
    rationale: str


def log_proposal(proposal: IMessageProposal) -> None:
    """Persist proposal to logs pending Phase E transport integration."""
    rationale_headline = proposal.rationale.splitlines()[0] if proposal.rationale else ""
    logger.info(
        "IMESSAGE_PROPOSAL_STUB ticker=%s side=%s stake=%.2f rationale=%s",
        proposal.ticker,
        proposal.side,
        proposal.stake_dollars,
        rationale_headline,
    )
