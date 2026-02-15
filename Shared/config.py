"""Central configuration — reads from environment, never hardcodes secrets."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from repo root
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

class Config:
    CODEX_API_KEY = os.getenv("CODEX_API_KEY")
    KALSHI_API_KEY = os.getenv("KALSHI_API_KEY")
    KALSHI_API_SECRET = os.getenv("KALSHI_API_SECRET")
    KALSHI_ENV = os.getenv("KALSHI_ENV", "DEMO")

    # Bankroll constraints
    BANKROLL_START = 50.00
    MAX_TRADE_RISK = 0.50
    MAX_TOTAL_EXPOSURE = 2.00
    MAX_THEME_EXPOSURE = 5.00
    KELLY_FRACTION = 0.25
    MIN_EV_THRESHOLD = 0.40    # 40% EV minimum
    MIN_CONFIDENCE = 0.97      # 97% confidence minimum
    DRAWDOWN_DAILY_LIMIT = 0.25
    DRAWDOWN_WEEKLY_LIMIT = 1.00

    # iMessage whitelist (sole authorized number)
    IMESSAGE_WHITELIST = ["+17657921945"]
