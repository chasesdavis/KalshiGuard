#!/usr/bin/env bash
set -euo pipefail

# Resolve merge conflicts for one or more feature branches by merging latest main.
# Usage:
#   ./scripts/resolve-pr-conflicts.sh <feature-branch> [feature-branch...]
#   ./scripts/resolve-pr-conflicts.sh
#
# Example (two remaining PR branches):
#   ./scripts/resolve-pr-conflicts.sh codex/pr-3 codex/pr-4

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ Not inside a git repository." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "❌ Working tree is not clean. Commit or stash changes first." >&2
  exit 1
fi

discover_unpushed_branches() {
  local branch
  local ahead_count

  while IFS= read -r branch; do
    # Focus this helper on PR branches only.
    [[ "${branch}" =~ ^codex/pr- ]] || continue

    if ! git show-ref --verify --quiet "refs/remotes/origin/${branch}"; then
      echo "${branch}"
      continue
    fi

    ahead_count="$(git rev-list --count "origin/${branch}..${branch}")"
    if [[ "${ahead_count}" -gt 0 ]]; then
      echo "${branch}"
    fi
  done < <(git for-each-ref --format='%(refname:short)' refs/heads)
}

if [[ "$#" -eq 0 ]]; then
  mapfile -t auto_branches < <(discover_unpushed_branches)
  if [[ "${#auto_branches[@]}" -eq 0 ]]; then
    echo "ℹ️ No local unpushed PR branches found (pattern: codex/pr-*)."
    exit 0
  fi
  set -- "${auto_branches[@]}"
  echo "➡️ Auto-detected unpushed PR branches: $*"
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "❌ Missing 'origin' remote; cannot sync PR branches to GitHub." >&2
  exit 1
fi

echo "➡️ Fetching latest refs from origin..."
git fetch origin --prune

for feature_branch in "$@"; do
  echo
  echo "=== Processing ${feature_branch} ==="
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
    echo "⚠️ Merge conflicts detected on ${feature_branch}. Resolve files, then run:"
    echo "   git add <resolved-files>"
    echo "   git commit"
    echo "   git push origin ${feature_branch}"
    echo
    echo "Tip: list conflicted files with: git diff --name-only --diff-filter=U"
    exit 2
  fi

  echo "✅ Merge completed without conflicts for ${feature_branch}."
  echo "➡️ Running tests..."
  ./scripts/run-tests.sh

  echo "➡️ Pushing updated branch"
  git push origin "${feature_branch}"

done

echo

echo "✅ Done. Branches were updated and pushed."
