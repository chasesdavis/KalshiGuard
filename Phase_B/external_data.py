"""External calibration sources for Phase B.

This module intentionally defaults to deterministic mock anchors so the analysis engine
can run offline and in CI without third-party dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExternalAnchor:
    """Normalized external reference probability for a market."""

    source: str
    probability_yes: float
    confidence: float
    context: str


class ExternalDataProvider:
    """Provides external probability anchors.

    Phase B uses mock/stub anchors that emulate feeds such as CME, FRED, and NOAA.
    The interface is production-oriented so live adapters can replace these methods
    without changing downstream analysis code.
    """

    _MOCK_ANCHORS: dict[str, list[ExternalAnchor]] = {
        "FED-RATE-25MAR": [
            ExternalAnchor("cme_fedwatch", 0.70, 0.86, "CME watch implies hold probability near 70%"),
            ExternalAnchor("fred_rates_regime", 0.67, 0.72, "FRED regime score favors policy hold"),
            ExternalAnchor("internal_macro_model", 0.73, 0.75, "Macro nowcast supports hold scenario"),
        ],
        "WEATHER-NYC-SNOW": [
            ExternalAnchor("noaa_blend", 0.40, 0.78, "NOAA blend puts major snowfall odds around 40%"),
            ExternalAnchor("ecmwf_consensus", 0.36, 0.74, "ECMWF trend is below contract implication"),
            ExternalAnchor("internal_weather_model", 0.42, 0.70, "Internal weather model slight bullish snow tilt"),
        ],
    }

    def get_probability_anchors(self, ticker: str) -> list[ExternalAnchor]:
        """Return available anchors for a market ticker.

        Unknown tickers return a conservative fallback set with low confidence.
        """
        anchors = self._MOCK_ANCHORS.get(ticker)
        if anchors:
            return anchors

        return [
            ExternalAnchor(
                source="fallback_baseline",
                probability_yes=0.50,
                confidence=0.45,
                context="No external coverage; using neutral baseline",
            )
        ]

    def get_source_payload(self, ticker: str) -> dict[str, Any]:
        """Structured payload useful for logging and API explanations."""
        anchors = self.get_probability_anchors(ticker)
        return {
            "ticker": ticker,
            "sources": [
                {
                    "name": anchor.source,
                    "probability_yes": anchor.probability_yes,
                    "confidence": anchor.confidence,
                    "context": anchor.context,
                }
                for anchor in anchors
            ],
        }
