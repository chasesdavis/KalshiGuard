"""Phase A compatibility layer delegating analysis to Phase B engine."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Phase_B.analysis_engine import AnalysisResult, PhaseBAnalysisEngine, ProposalResult
from Shared.models import EVSignal, PriceSnapshot

_ENGINE = PhaseBAnalysisEngine()


def compute_ev_for_signal(ticker: str, snapshot: PriceSnapshot) -> EVSignal:
    """Return EV signal for API compatibility."""
    if ticker != snapshot.ticker:
        snapshot = PriceSnapshot(
            ticker=ticker,
            timestamp=snapshot.timestamp,
            yes_bid=snapshot.yes_bid,
            yes_ask=snapshot.yes_ask,
            no_bid=snapshot.no_bid,
            no_ask=snapshot.no_ask,
            volume=snapshot.volume,
            open_interest=snapshot.open_interest,
        )
    return _ENGINE.analyze_snapshot(snapshot).signal


def analyze_snapshot_with_context(snapshot: PriceSnapshot) -> AnalysisResult:
    """Expose full Phase B context for structured API responses."""
    return _ENGINE.analyze_snapshot(snapshot)


def propose_trade_with_context(snapshot: PriceSnapshot) -> ProposalResult:
    """Create a human-approval trade proposal after Phase B + C checks."""
    return _ENGINE.propose_trade(snapshot)
