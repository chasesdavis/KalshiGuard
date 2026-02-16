"""Kalshi demo API connector for paper trading workflows.

Uses demo credentials from environment when available. Falls back to Phase A mock data
for offline/local deterministic operation.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import requests

from Phase_A.data_fetcher import fetch_price_snapshots
from Shared.config import Config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DemoCredentialsStatus:
    api_key_set: bool
    api_secret_set: bool
    signup_url: str = "https://demo.kalshi.co/"


class DemoKalshiConnector:
    """Read-only connector for demo exchange market snapshots."""

    base_url: str = "https://demo-api.kalshi.co/trade-api/v2"

    def __init__(self) -> None:
        self.api_key = Config.DEMO_KALSHI_API_KEY
        self.api_secret = Config.DEMO_KALSHI_API_SECRET

    def credentials_status(self) -> DemoCredentialsStatus:
        return DemoCredentialsStatus(api_key_set=bool(self.api_key), api_secret_set=bool(self.api_secret))

    def fetch_market_snapshot(self, ticker: str) -> dict[str, Any]:
        """Fetch one market from demo API; fallback to local mock snapshot if unavailable."""
        try:
            payload = self._fetch_remote_market(ticker)
            if payload:
                return payload
        except requests.RequestException as exc:
            logger.warning("Demo API unavailable for %s; using mock snapshot. error=%s", ticker, exc)

        snapshot_lookup = {s.ticker: s for s in fetch_price_snapshots()}
        snap = snapshot_lookup.get(ticker)
        if not snap:
            raise ValueError(f"Ticker not found in demo or local fallback: {ticker}")

        return {
            "ticker": snap.ticker,
            "yes_ask": snap.yes_ask,
            "no_ask": snap.no_ask,
            "yes_bid": snap.yes_bid,
            "no_bid": snap.no_bid,
            "volume": snap.volume,
            "open_interest": snap.open_interest,
            "source": "local_mock",
        }

    def _fetch_remote_market(self, ticker: str) -> dict[str, Any] | None:
        endpoint = f"{self.base_url}/markets/{ticker}"
        headers = {}
        if self.api_key:
            headers["KALSHI-ACCESS-KEY"] = self.api_key

        response = requests.get(endpoint, timeout=10, headers=headers)
        if response.status_code >= 400:
            return None

        payload = response.json()
        market = payload.get("market") or payload
        yes_ask = market.get("yes_ask") or market.get("yes_ask_price")
        no_ask = market.get("no_ask") or market.get("no_ask_price")
        yes_bid = market.get("yes_bid") or market.get("yes_bid_price")
        no_bid = market.get("no_bid") or market.get("no_bid_price")

        if yes_ask is None or no_ask is None:
            return None

        return {
            "ticker": ticker,
            "yes_ask": float(yes_ask),
            "no_ask": float(no_ask),
            "yes_bid": float(yes_bid or max(0.0, yes_ask - 2)),
            "no_bid": float(no_bid or max(0.0, no_ask - 2)),
            "volume": int(market.get("volume", 0)),
            "open_interest": int(market.get("open_interest", 0)),
            "source": "demo_api",
        }
