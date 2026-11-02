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

echo "Installing Python 3.11 and ffmpeg (skips anything already installed)..."
brew install python@3.11 ffmpeg

ENV_DIR="$HOME/Library/Application Support/saxscribe/python"
if [ ! -x "$ENV_DIR/bin/python" ]; then
  echo "Creating a private Python environment in $ENV_DIR ..."
  mkdir -p "$(dirname "$ENV_DIR")"
  "$(brew --prefix python@3.11)/bin/python3.11" -m venv "$ENV_DIR"
fi
if [ ! -e .venv ] || [ -L .venv ]; then
  ln -sfn "$ENV_DIR" .venv
fi
source "$ENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

echo
python -m saxscribe check
echo
echo "Done. In each new Terminal window, run this first:"
echo "  source .venv/bin/activate"
echo "Then transcribe a take with:"
echo "  python -m saxscribe transcribe ~/Music/take.wav"
