#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source venv/bin/activate 2>/dev/null || true
echo "🛡️ Starting KalshiGuard Flask API on http://localhost:5000"
python Phase_A/api.py
