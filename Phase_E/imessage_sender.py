"""iMessage proposal sender and approval listener.

Outbound delivery uses a BlueBubbles server via an OpenClaw-style HTTP bridge when
configured through environment variables. In local/test mode without bridge config,
messages are queued in-memory only.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass

import requests

from Shared.config import Config

APPROVAL_PATTERN = re.compile(r"^APPROVE\s+TRADE\s+ID\s+(?P<trade_id>[A-Z0-9\-]+)$", re.IGNORECASE)


@dataclass(frozen=True)
class ApprovalMessage:
    """Inbound approval message envelope."""

    from_number: str
    body: str


class IMessageSender:
    """Whitelisted iMessage notifier with approval polling."""

    def __init__(self) -> None:
        self._whitelist = set(Config.IMESSAGE_WHITELIST)
        self._inbox: list[ApprovalMessage] = []
        self._outbox: list[dict[str, str]] = []

    def _is_bridge_enabled(self) -> bool:
        return bool(Config.BLUEBUBBLES_SERVER_URL and Config.OPENCLAW_API_KEY)

    def send_trade_proposal(self, to_number: str, message: str) -> dict[str, str]:
        """Send proposal message to an approved number only.

        If BlueBubbles/OpenClaw bridge config is present, sends over HTTP to the
        configured OpenClaw endpoint. Otherwise records a local queued message.
        """
        if to_number not in self._whitelist:
            raise PermissionError("Recipient is not in iMessage approval whitelist.")

        if self._is_bridge_enabled():
            bridge_url = f"{Config.BLUEBUBBLES_SERVER_URL.rstrip('/')}{Config.OPENCLAW_SEND_PATH}"
            response = requests.post(
                bridge_url,
                json={
                    "service": "iMessage",
                    "recipient": to_number,
                    "message": message,
                },
                headers={
                    "Authorization": f"Bearer {Config.OPENCLAW_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json() if response.content else {}
            outbound = {
                "to": to_number,
                "message": message,
                "status": payload.get("status", "sent"),
                "provider": "bluebubbles-openclaw",
            }
        else:
            outbound = {
                "to": to_number,
                "message": message,
                "status": "queued",
                "provider": "local-dev-queue",
            }

        self._outbox.append(outbound)
        return outbound

    def record_incoming_message(self, from_number: str, body: str) -> None:
        """Record inbound message from webhook/bridge process."""
        self._inbox.append(ApprovalMessage(from_number=from_number, body=body.strip()))

    def wait_for_trade_approval(
        self,
        trade_id: str,
        timeout_seconds: int | None = None,
        poll_interval_seconds: float = 1.0,
    ) -> bool:
        """Poll inbox for explicit trade approval from the whitelisted number."""
        timeout = timeout_seconds if timeout_seconds is not None else Config.APPROVAL_WAIT_TIMEOUT_SECONDS
        deadline = time.time() + timeout
        expected = trade_id.upper()

        while time.time() < deadline:
            for message in list(self._inbox):
                if message.from_number not in self._whitelist:
                    continue
                match = APPROVAL_PATTERN.match(message.body)
                if not match:
                    continue
                if match.group("trade_id").upper() == expected:
                    return True
            time.sleep(poll_interval_seconds)
        return False

    @property
    def outbox(self) -> list[dict[str, str]]:
        """Return a copy of sent/queued messages."""
        return list(self._outbox)
