#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "🧪 Running Phase A-H test suite..."
if [ -x "./venv/bin/python" ]; then
  ./venv/bin/python -m pytest Phase_A/tests Phase_B/tests Phase_C/tests Phase_D/tests Phase_E/tests Phase_F/tests Phase_H/tests -v
else
  python3 -m pytest Phase_A/tests Phase_B/tests Phase_C/tests Phase_D/tests Phase_E/tests Phase_F/tests Phase_H/tests -v
fi
