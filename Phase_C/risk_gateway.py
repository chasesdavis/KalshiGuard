"""Risk gateway for Phase C/Phase E integration.

Applies hard bankroll and confidence limits before any live proposal.
"""
from __future__ import annotations

from dataclasses import dataclass

from Shared.config import Config
from Shared.models import EVSignal, PriceSnapshot


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reason: str
    max_contracts: int
    estimated_risk_dollars: float


class RiskGateway:
    """Evaluates whether a trade may proceed to human-approval stage."""

    def assess(self, signal: EVSignal, snapshot: PriceSnapshot, bankroll: float = Config.BANKROLL_START) -> RiskDecision:
        if signal.side not in {"YES", "NO"}:
            return RiskDecision(False, "Signal side is HOLD; no trade proposal allowed.", 0, 0.0)
        if signal.ev_percent < Config.MIN_EV_THRESHOLD:
            return RiskDecision(False, "EV below minimum threshold.", 0, 0.0)
        if signal.confidence < Config.MIN_CONFIDENCE:
            return RiskDecision(False, "Confidence below minimum threshold.", 0, 0.0)
        if bankroll < 40:
            return RiskDecision(False, "Buying power below $40 freeze threshold.", 0, 0.0)

        ask_price = snapshot.yes_ask if signal.side == "YES" else snapshot.no_ask
        dollars_per_contract = max(ask_price / 100.0, 0.01)
        max_contracts = int(Config.MAX_TRADE_RISK // dollars_per_contract)
        if max_contracts < 1:
            return RiskDecision(False, "Contract price exceeds per-trade risk cap.", 0, 0.0)

        estimated_risk = round(max_contracts * dollars_per_contract, 2)
        return RiskDecision(True, "Pass", max_contracts, estimated_risk)
