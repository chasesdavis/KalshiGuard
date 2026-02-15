#!/bin/bash
set -e
echo "🛡️  Setting up KalshiGuard environment..."
cd "$(dirname "$0")/.."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env 2>/dev/null || true
echo "✅ Done. Activate with: source venv/bin/activate"
echo "   Then run Phase A: python Phase_A/api.py"
