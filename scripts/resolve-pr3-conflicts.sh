#!/usr/bin/env bash
set -euo pipefail

# Resolve conflicts for PR #3 by updating a local branch with latest main.
# Usage:
#   ./scripts/resolve-pr3-conflicts.sh [feature-branch]
#
# Defaults:
#   feature-branch: current branch

feature_branch="${1:-$(git rev-parse --abbrev-ref HEAD)}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ Not inside a git repository." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "❌ Working tree is not clean. Commit or stash changes first." >&2
  exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "❌ Missing 'origin' remote." >&2
  exit 1
fi

echo "➡️ Fetching latest refs from origin..."
git fetch origin --prune

echo "➡️ Checking out branch: ${feature_branch}"
git checkout "${feature_branch}"

# Make sure local branch is up-to-date with remote tracking branch when available.
if git show-ref --verify --quiet "refs/remotes/origin/${feature_branch}"; then
  echo "➡️ Rebasing ${feature_branch} onto origin/${feature_branch}"
  git rebase "origin/${feature_branch}"
fi

echo "➡️ Merging origin/main into ${feature_branch}"
set +e
git merge origin/main
merge_status=$?
set -e

if [[ ${merge_status} -ne 0 ]]; then
  echo
  echo "⚠️ Merge conflicts detected. Resolve files, then run:"
  echo "   git add <resolved-files>"
  echo "   git commit"
  echo "   git push origin ${feature_branch}"
  echo
  echo "Tip: list conflicted files with: git diff --name-only --diff-filter=U"
  exit 2
fi

echo "✅ Merge completed without conflicts."
echo "➡️ Running tests..."
./scripts/run-tests.sh

echo "➡️ Pushing updated branch"
git push origin "${feature_branch}"

echo "✅ Done. PR should now be mergeable (or have only manual conflict leftovers if any)."
