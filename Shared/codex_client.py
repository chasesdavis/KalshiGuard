"""Codex Cloud client wrapper.

Reads API key from env and fails gracefully when unavailable.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from Shared.config import Config

logger = logging.getLogger(__name__)


@dataclass
class CodexClient:
    """Minimal wrapper around chat-completions for optional code-assist workflows."""

    endpoint: str = "https://api.openai.com/v1/chat/completions"
    model: str = "gpt-4o"

    def is_available(self) -> bool:
        return bool(Config.CODEX_API_KEY)

    def generate_text(self, prompt: str, temperature: float = 0.2, max_tokens: int = 1024) -> str | None:
        if not self.is_available():
            logger.info("CODEX_API_KEY is not configured; skipping Codex request.")
            return None

        headers = {
            "Authorization": f"Bearer {Config.CODEX_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=45)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.RequestException as exc:
            logger.error("Codex request failed: %s", exc)
            return None


def get_codex_client() -> CodexClient:
    """Factory for convenience in call sites."""
    return CodexClient()
