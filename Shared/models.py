"""Shared data models used across all phases."""
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Market:
    ticker: str
    title: str
    subtitle: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None

@dataclass
class Event:
    event_id: str
    market_ticker: str
    description: str

@dataclass
class PriceSnapshot:
    ticker: str
    timestamp: str
    yes_bid: float
    yes_ask: float
    no_bid: float
    no_ask: float
    volume: int = 0
    open_interest: int = 0

@dataclass
class EVSignal:
    ticker: str
    ev_percent: float
    confidence: float
    explanation: str
    data_sources: List[str] = field(default_factory=list)
    side: str = "HOLD"
