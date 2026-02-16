#!/usr/bin/env python3
"""Container healthcheck for KalshiGuard Flask API."""
from __future__ import annotations

import sys

import requests


def main() -> int:
    try:
        resp = requests.get("http://127.0.0.1:5000/health", timeout=5)
        if resp.status_code == 200:
            return 0
        return 1
    except requests.RequestException:
        return 1


if __name__ == "__main__":
    sys.exit(main())
