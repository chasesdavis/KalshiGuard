#!/bin/bash
set -e
cd "$(dirname "$0")/.."
source venv/bin/activate 2>/dev/null || true
echo "🛡️  Starting KalshiGuard Phase A API on http://localhost:5000 ..."
python Phase_A/api.py
