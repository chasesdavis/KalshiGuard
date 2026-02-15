#!/bin/bash
set -e
cd "$(dirname "$0")/.."
source venv/bin/activate 2>/dev/null || true
echo "🧪 Running Phase A tests..."
python -m pytest Phase_A/tests/ -v
