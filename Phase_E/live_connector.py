"""Kalshi live API connector with request signing.

Uses API key/secret from environment (via Shared.config.Config) and signs
requests with HMAC-SHA256 over timestamp + method + path + body.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any

import requests

from Shared.config import Config


@dataclass
class KalshiLiveConnector:
    """HTTP connector for Kalshi trade API v2 endpoints."""

    base_url: str = "https://trading-api.kalshi.com/trade-api/v2"
    timeout_s: int = 20

    def _headers(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, str]:
        if not Config.KALSHI_API_KEY or not Config.KALSHI_API_SECRET:
            raise RuntimeError("KALSHI_API_KEY and KALSHI_API_SECRET are required for live operations.")

        timestamp_ms = str(int(time.time() * 1000))
        body_str = json.dumps(body, separators=(",", ":"), sort_keys=True) if body else ""
        message = f"{timestamp_ms}{method.upper()}{path}{body_str}".encode("utf-8")
        digest = hmac.new(
            Config.KALSHI_API_SECRET.encode("utf-8"),
            message,
            hashlib.sha256,
        ).digest()
        signature = base64.b64encode(digest).decode("utf-8")
        return {
            "KALSHI-ACCESS-KEY": Config.KALSHI_API_KEY,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": timestamp_ms,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = self._headers(method, path, body)
        response = requests.request(method, url, headers=headers, json=body, timeout=self.timeout_s)
        response.raise_for_status()
        return response.json() if response.content else {"status": "ok"}

    def place_order(self, order: dict[str, Any]) -> dict[str, Any]:
        """Place order. Maps internal fields to Kalshi-compatible payload."""
        payload = {
            "ticker": order["ticker"],
            "side": order["side"].upper(),
            "count": order["contracts"],
            "type": order.get("order_type", "market").upper(),
        }
        if order.get("limit_price_cents") is not None:
            payload["price"] = order["limit_price_cents"]
        if order.get("client_order_id"):
            payload["client_order_id"] = order["client_order_id"]

        return self._request("POST", "/portfolio/orders", payload)

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        """Cancel existing order."""
        return self._request("DELETE", f"/portfolio/orders/{order_id}")
