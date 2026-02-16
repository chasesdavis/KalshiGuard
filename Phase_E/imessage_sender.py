"""iMessage proposal sender and approval listener.

Production deployments can wire SMS/iMessage providers externally and push
incoming messages via ``record_incoming_message``.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass

from Shared.config import Config

APPROVAL_PATTERN = re.compile(r"^APPROVE\s+TRADE\s+ID\s+(?P<trade_id>[A-Z0-9\-]+)$", re.IGNORECASE)


@dataclass(frozen=True)
class ApprovalMessage:
    from_number: str
    body: str


class IMessageSender:
    """Whitelisted iMessage/SMS notifier with approval polling."""

    def __init__(self) -> None:
        self._whitelist = set(Config.IMESSAGE_WHITELIST)
        self._inbox: list[ApprovalMessage] = []
        self._outbox: list[dict[str, str]] = []

    def send_trade_proposal(self, to_number: str, message: str) -> dict[str, str]:
        """Send a proposal message to the approved number only."""
        if to_number not in self._whitelist:
            raise PermissionError("Recipient is not in iMessage approval whitelist.")
        outbound = {"to": to_number, "message": message, "status": "queued"}
        self._outbox.append(outbound)
        # Integration hook: replace this in production with Twilio or AppleScript transport.
        return outbound

    def record_incoming_message(self, from_number: str, body: str) -> None:
        """Record inbound message from webhook/bridge process."""
        self._inbox.append(ApprovalMessage(from_number=from_number, body=body.strip()))

    def wait_for_trade_approval(
        self,
        trade_id: str,
        timeout_seconds: int = 60,
        poll_interval_seconds: float = 1.0,
    ) -> bool:
        """Poll inbox for explicit trade approval from the whitelisted number."""
        deadline = time.time() + timeout_seconds
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
        return list(self._outbox)
