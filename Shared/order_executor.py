"""Shared order execution façade used by live-trading workflows.

This module centralizes order payload normalization and routes order placement
through the Phase E live connector.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from Phase_E.live_connector import KalshiLiveConnector

OrderSide = Literal["yes", "no"]
OrderType = Literal["market", "limit"]


@dataclass(frozen=True)
class OrderRequest:
    """Represents a validated order request for Kalshi execution."""

    ticker: str
    side: OrderSide
    contracts: int
    order_type: OrderType = "market"
    limit_price_cents: int | None = None
    client_order_id: str | None = None


@dataclass(frozen=True)
class OrderResult:
    """Represents connector response for an order action."""

    status: str
    order_id: str | None
    raw: dict


class OrderExecutor:
    """Thin execution layer around :class:`KalshiLiveConnector`."""

    def __init__(self, connector: KalshiLiveConnector | None = None) -> None:
        self.connector = connector or KalshiLiveConnector()

    def place_order(self, request: OrderRequest) -> OrderResult:
        """Submit a market or limit order for YES/NO side."""
        payload = asdict(request)
        response = self.connector.place_order(payload)
        return OrderResult(
            status=response.get("status", "unknown"),
            order_id=response.get("order_id"),
            raw=response,
        )

    def cancel_order(self, order_id: str) -> OrderResult:
        """Cancel a previously submitted order."""
        response = self.connector.cancel_order(order_id)
        return OrderResult(
            status=response.get("status", "unknown"),
            order_id=order_id,
            raw=response,
        )
