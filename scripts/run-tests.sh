#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source venv/bin/activate 2>/dev/null || true
echo "🧪 Running Phase A + Phase B + Phase C tests..."
python -m pytest Phase_A/tests Phase_B/tests Phase_C/tests -v
