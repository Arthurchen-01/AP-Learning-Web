#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/publish-mini-ap-tracker.sh [target_repo_url] [target_dir]
#
# Example:
#   ./scripts/publish-mini-ap-tracker.sh https://github.com/Arthurchen-01/ap-tracker .

TARGET_REPO_URL="${1:-https://github.com/Arthurchen-01/ap-tracker}"
TARGET_DIR="${2:-.}"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "[1/6] Cloning target repo: $TARGET_REPO_URL"
git clone "$TARGET_REPO_URL" "$WORKDIR/target"

echo "[2/6] Copying mini-ap-tracker into target repo root: $TARGET_DIR"
mkdir -p "$WORKDIR/target/$TARGET_DIR"
rsync -a --delete "mini-ap-tracker/" "$WORKDIR/target/$TARGET_DIR/"

echo "[3/6] Git status after copy"
cd "$WORKDIR/target"
git status --short

echo "[4/6] Committing changes"
git add -A
if git diff --cached --quiet; then
  echo "No changes to commit."
  exit 0
fi

git commit -m "chore: sync mini-ap-tracker from AP-Learning-Web"

echo "[5/6] Pushing to origin"
git push origin HEAD

echo "[6/6] Done"
