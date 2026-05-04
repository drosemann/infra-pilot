#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")"/.. >/dev/null 2>&1; pwd)"
python3 "$SCRIPT_DIR/scripts/coverage_badge_updater.py"
if [ ! -f README.md ]; then
  echo "README.md not found; skipping badge update commit." >&2
  exit 0
fi

git status --porcelain >/dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Git not available or not a git repo; skipping badge update commit." >&2
  exit 0
fi

changes=$(git status --porcelain README.md | wc -l)
if [ "$changes" -eq 0 ]; then
  echo "No changes to README.md; badge already up-to-date." 
  exit 0
fi

git config user.name "InfraPilot CI Bot"
git config user.email "ci-bot@example.com"
git add README.md
git commit -m "ci: update README coverage badge" || true
git push origin HEAD
