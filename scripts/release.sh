#!/usr/bin/env bash
set -euo pipefail

#############################################
# Lightweight Release Script
# Usage: ./scripts/release.sh -t <tag> [-m <message>] [-c] [-p]
#  -t, --tag        Tag name for the release (e.g., v1.2.3)
#  -m, --message    Release message (default: "Release <tag>")
#  -c, --changelog  Update CHANGELOG.md with entry for this release
#  -p, --push       Push the tag (and changelog commit if updated) to origin
#############################################

SCRIPT_NAME="release"

TAG=""
MESSAGE=""
UPDATE_CHANGELOG=false
PUSH=false

print_usage() {
  echo "Usage: ./scripts/release.sh -t <tag> [-m <message>] [-c] [-p]" \
    "| --tag <tag> --message <message> --changelog --push"
  echo "\nOptions:"
  echo "  -t, --tag        Release tag name (e.g., v1.2.3)"
  echo "  -m, --message    Release message (default: 'Release <tag>')"
  echo "  -c, --changelog  Update CHANGELOG.md with an entry for this release"
  echo "  -p, --push       Push the tag and any changelog commits to origin"
}

# Manual lightweight arg parsing (support short and long forms)
while [[ $# -gt 0 ]]; do
  case "$1" in
    -t|--tag)
      TAG="$2"; shift 2;;
    -m|--message)
      MESSAGE="$2"; shift 2;;
    -c|--changelog)
      UPDATE_CHANGELOG=true; shift;;
    -p|--push)
      PUSH=true; shift;;
    -h|--help)
      print_usage; exit 0;;
    *)
      echo "Unknown option: $1"; print_usage; exit 1;;
  esac
done

if [[ -z "$TAG" ]]; then
  echo "Error: Tag must be provided with -t or --tag";
  print_usage; exit 1
fi

if [[ -z "$MESSAGE" ]]; then
  MESSAGE="Release ${TAG}"
fi

echo "[${SCRIPT_NAME}] Preparing release for tag: ${TAG}"

# Pick random release artwork
RELEASE_ART=$(find images-for-releases -maxdepth 1 -name '*.png' 2>/dev/null | shuf -n1)
if [[ -n "$RELEASE_ART" ]]; then
  mkdir -p branding
  cp "$RELEASE_ART" branding/release-art.png
  echo "[${SCRIPT_NAME}] Selected release artwork: $RELEASE_ART"
fi

# Ensure clean working tree
git status --porcelain >/dev/null || true
if ! git diff --quiet HEAD; then
  echo "Error: Working tree is not clean. Commit or stash changes before releasing.";
  exit 1
fi

# Create annotated tag
git tag -a "$TAG" -m "$MESSAGE"
echo "Created annotated tag ${TAG}"

# Optional changelog update
if [[ "$UPDATE_CHANGELOG" == true ]]; then
  CHANGELOG_FILE="CHANGELOG.md"
  DATE=$(date +"%Y-%m-%d")
  ENTRY_HEADING="\n## ${TAG} - ${DATE}\n\n- Release: ${MESSAGE}\n"
  if [[ -f "$CHANGELOG_FILE" ]]; then
    printf "%s" "$ENTRY_HEADING" >> "$CHANGELOG_FILE"
  else
    printf "# Changelog\n%s" "$ENTRY_HEADING" > "$CHANGELOG_FILE"
  fi
  git add CHANGELOG.md
  git commit -m "docs: update changelog for ${TAG}"
  echo "CHANGELOG.md updated for ${TAG}"
fi

# Push if requested
if [[ "$PUSH" == true ]]; then
  git push origin "$TAG"
  echo "Pushed tag ${TAG} to origin"

  # Upload release artwork if one was picked
  if [[ -f branding/release-art.png ]]; then
    gh release upload "$TAG" branding/release-art.png --clobber 2>/dev/null || \
      echo "[${SCRIPT_NAME}] Warning: gh release upload failed (install GitHub CLI?)"
  fi
fi

echo "Release scaffold complete."
