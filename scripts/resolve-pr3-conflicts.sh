#!/usr/bin/env bash
set -euo pipefail

# Backward-compatible wrapper.
# Prefer: ./scripts/resolve-pr-conflicts.sh <feature-branch> [feature-branch...]

feature_branch="${1:-$(git rev-parse --abbrev-ref HEAD)}"
exec "$(dirname "$0")/resolve-pr-conflicts.sh" "${feature_branch}"
