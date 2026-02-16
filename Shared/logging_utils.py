"""Shared logging helpers."""
from __future__ import annotations

import logging


def configure_logging(level: int = logging.INFO) -> None:
    """Configure consistent application logging once per process."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
