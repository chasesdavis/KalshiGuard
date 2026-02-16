"""Central configuration loader.

Environment values are sourced from `.env` at repository root when present.
No secrets are hardcoded.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


class Config:
    """Application configuration constants and env-backed secrets."""

    CODEX_API_KEY = os.getenv("CODEX_API_KEY")
    KALSHI_API_KEY = os.getenv("KALSHI_API_KEY")
    KALSHI_API_SECRET = os.getenv("KALSHI_API_SECRET")
    DEMO_KALSHI_API_KEY = os.getenv("DEMO_KALSHI_API_KEY")
    DEMO_KALSHI_API_SECRET = os.getenv("DEMO_KALSHI_API_SECRET")
    KALSHI_ENV = os.getenv("KALSHI_ENV", "DEMO")

    # Bankroll constraints
    BANKROLL_START = 50.00
    MAX_TRADE_RISK = 0.50
    MAX_TOTAL_EXPOSURE = 2.00
    MAX_THEME_EXPOSURE = 5.00
    KELLY_FRACTION = 0.25
    MIN_EV_THRESHOLD = 0.40
    MIN_CONFIDENCE = 0.97
    MIN_CONFIRMATIONS = 4
    DRAWDOWN_DAILY_LIMIT = 0.25
    DRAWDOWN_WEEKLY_LIMIT = 1.00

    # iMessage whitelist (sole authorized number)
    IMESSAGE_WHITELIST = ["+17657921945"]

    @classmethod
    def is_codex_enabled(cls) -> bool:
        return bool(cls.CODEX_API_KEY)
