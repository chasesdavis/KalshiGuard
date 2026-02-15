"""Phase A analysis — placeholder EV engine with structured explanations."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from Shared.models import EVSignal

def compute_ev_for_signal(ticker, snapshot) -> EVSignal:
    """
    Compute expected value for a market snapshot.
    Phase A: conservative placeholder (always returns HOLD).
    Phase B+ will plug in real probability models.
    """
    implied_yes = snapshot.yes_ask / 100.0
    implied_no = snapshot.no_ask / 100.0
    spread = snapshot.yes_ask - snapshot.yes_bid

    # Phase A: no edge claimed — just report market state
    ev = 0.0
    confidence = 0.0
    side = "HOLD"

    explanation = (
        f"Market: {ticker}\n"
        f"  YES price: {snapshot.yes_bid}–{snapshot.yes_ask}¢ (implied {implied_yes:.0%})\n"
        f"  NO  price: {snapshot.no_bid}–{snapshot.no_ask}¢ (implied {implied_no:.0%})\n"
        f"  Spread: {spread}¢ | Volume: {snapshot.volume:,} | OI: {snapshot.open_interest:,}\n"
        f"  Phase A verdict: HOLD (no model edge claimed yet)\n"
        f"  ⚠️  Requires Phase B analysis engine for real EV estimates."
    )

    return EVSignal(
        ticker=ticker,
        ev_percent=ev,
        confidence=confidence,
        explanation=explanation,
        data_sources=["mock_orderbook"],
        side=side,
    )
