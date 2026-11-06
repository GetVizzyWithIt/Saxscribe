#!/bin/bash
# Regenerate requirements.lock from requirements.txt (needs uv: brew install uv).
# Versions in scripts/scorecard-versions.txt are held fixed.
set -e
cd "$(dirname "$0")/.."
BODY=$(mktemp)
uv pip compile --python-version "$(cat .python-version)" --python-platform aarch64-apple-darwin \
  --no-header requirements.txt -c scripts/scorecard-versions.txt -o "$BODY"
{ sed -n '1,/^$/p' requirements.lock; cat "$BODY"; } > requirements.lock.new
mv requirements.lock.new requirements.lock
rm -f "$BODY"
echo "requirements.lock updated. Commit it with requirements.txt."
