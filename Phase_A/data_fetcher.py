"""Read-only data fetcher — mock data for Phase A scaffold."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from Shared.models import Market, PriceSnapshot

def fetch_markets():
    """Return mock markets. Replace with real Kalshi API calls in Phase B+."""
    return [
        Market(ticker="FED-RATE-25MAR", title="Fed holds rates in March 2026",
               subtitle="Will the Fed hold rates at current level?",
               category="Economics", status="open"),
        Market(ticker="WEATHER-NYC-SNOW", title="NYC snowfall > 6 inches this week",
               category="Weather", status="open"),
    ]

def fetch_price_snapshots():
    """Return mock price snapshots."""
    return [
        PriceSnapshot(ticker="FED-RATE-25MAR", timestamp="2026-02-15T12:00:00Z",
                       yes_bid=72, yes_ask=74, no_bid=26, no_ask=28,
                       volume=45000, open_interest=820000),
        PriceSnapshot(ticker="WEATHER-NYC-SNOW", timestamp="2026-02-15T12:00:00Z",
                       yes_bid=35, yes_ask=38, no_bid=62, no_ask=65,
                       volume=8200, open_interest=95000),
    ]
