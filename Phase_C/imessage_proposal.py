"""Phase C iMessage proposal formatter (logging-only stub)."""
from __future__ import annotations

import logging
from typing import Any

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
