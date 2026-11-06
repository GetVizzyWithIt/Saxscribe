#!/bin/bash
# One-time setup on a Mac. Run from the repo folder:
#   bash setup_mac.sh
# Same layout as the Songs in the Key of Life analyzer, but its own environment,
# so the two projects never share installed packages by accident.
set -e

if ! command -v brew >/dev/null; then
  echo "Homebrew is needed first. Install it from https://brew.sh, then run this again."
  exit 1
fi

PY=$(cat .python-version)   # the one Python version this project runs on
echo "Installing Python $PY and ffmpeg (skips anything already installed)..."
brew install "python@$PY" ffmpeg

ENV_DIR="$HOME/Library/Application Support/saxscribe/python"
if [ ! -x "$ENV_DIR/bin/python" ]; then
  echo "Creating a private Python environment in $ENV_DIR ..."
  mkdir -p "$(dirname "$ENV_DIR")"
  "$(brew --prefix "python@$PY")/bin/python$PY" -m venv "$ENV_DIR"
fi
if [ ! -e .venv ] || [ -L .venv ]; then
  ln -sfn "$ENV_DIR" .venv
fi
source "$ENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.lock   # exact versions, so every install matches

echo
echo "Health check:"
if ! python -m saxscribe check; then
  echo "Setup finished, but the health check failed (see the -- lines above)."
  exit 1
fi
echo
echo "Done. In each new Terminal window, run this first:"
echo "  source .venv/bin/activate"
echo "Then transcribe a take with:"
echo "  python -m saxscribe transcribe ~/Music/take.wav"
