#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
python - <<'PY'
from Phase_A.data_fetcher import fetch_markets, fetch_price_snapshots

print("Markets:")
for market in fetch_markets():
    print(f"- {market.ticker}: {market.title}")

print("\nSnapshots:")
for snapshot in fetch_price_snapshots():
    print(
        f"- {snapshot.ticker} @ {snapshot.timestamp} | "
        f"YES {snapshot.yes_bid}/{snapshot.yes_ask} | "
        f"NO {snapshot.no_bid}/{snapshot.no_ask} | vol={snapshot.volume}"
    )
PY
