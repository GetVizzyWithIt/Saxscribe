#!/bin/bash
# Regenerate requirements.lock from requirements.txt (needs uv: brew install uv).
# Known-good versions of the models the scorecards were run with are held
# fixed here, so a relock never moves them by accident. Change them on purpose,
# in their own PR, with a scorecard.
set -e
cd "$(dirname "$0")/.."
KNOWN=$(mktemp)
cat > "$KNOWN" <<'PINS'
basic-pitch==0.4.0
torchcrepe==0.0.24
torch==2.8.0
torchaudio==2.8.0
demucs==4.1.0
librosa==0.11.0
music21==10.5.2
mir_eval==0.8.2
PINS
BODY=$(mktemp)
uv pip compile --python-version 3.11 --python-platform aarch64-apple-darwin \
  --no-header requirements.txt -c "$KNOWN" -o "$BODY"
{ sed -n '1,/^$/p' requirements.lock; cat "$BODY"; } > requirements.lock.new
mv requirements.lock.new requirements.lock
rm -f "$KNOWN" "$BODY"
echo "requirements.lock updated. Commit it with requirements.txt."
