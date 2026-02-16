"""Phase H alerting fanout across iMessage and Telegram."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests

from Phase_E.imessage_sender import IMessageSender
from Shared.config import Config
from Shared.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AlertResult:
    """Normalized alert send result."""

    channel: str
    status: str
    detail: str


class AlertingSystem:
    """Dispatch high-priority alerts to configured channels."""

    def __init__(self, audit_logger: AuditLogger | None = None, sender: IMessageSender | None = None) -> None:
        self.audit_logger = audit_logger
        self.sender = sender or IMessageSender()

    def send_alert(
        self,
        *,
        title: str,
        body: str,
        severity: str = "warning",
        channels: list[str] | None = None,
    ) -> list[AlertResult]:
        """Send alert to selected channels and record results."""

        channels = channels or Config.ALERT_CHANNELS
        message = f"[{severity.upper()}] {title}\n{body}".strip()
        results: list[AlertResult] = []

        for channel in channels:
            if channel == "imessage":
                results.append(self._send_imessage(message))
            elif channel == "telegram":
                results.append(self._send_telegram(message))
            else:
                results.append(AlertResult(channel=channel, status="skipped", detail="unknown_channel"))

        if self.audit_logger:
            self.audit_logger.log_event(
                component="alerting",
                event_type="alert_dispatch",
                severity=severity,
                message=title,
                payload={"channels": channels, "results": [r.__dict__ for r in results]},
            )
        return results

    def _send_imessage(self, message: str) -> AlertResult:
        to_number = Config.IMESSAGE_WHITELIST[0] if Config.IMESSAGE_WHITELIST else ""
        if not to_number:
            return AlertResult(channel="imessage", status="skipped", detail="no_whitelist_number")
        try:
            self.sender.send_trade_proposal(to_number, message)
            return AlertResult(channel="imessage", status="sent", detail="ok")
        except Exception as exc:  # pragma: no cover - defensive path
            logger.error("iMessage alert send failed: %s", exc)
            return AlertResult(channel="imessage", status="error", detail=str(exc))

    def _send_telegram(self, message: str) -> AlertResult:
        if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
            return AlertResult(channel="telegram", status="skipped", detail="telegram_not_configured")

        url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload: dict[str, Any] = {
            "chat_id": Config.TELEGRAM_CHAT_ID,
            "text": message,
            "disable_web_page_preview": True,
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return AlertResult(channel="telegram", status="sent", detail="ok")
        except requests.RequestException as exc:
            logger.error("Telegram alert send failed: %s", exc)
            return AlertResult(channel="telegram", status="error", detail=str(exc))
