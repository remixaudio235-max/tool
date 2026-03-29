#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=================================="
echo "   BeatStyle – Desktop App"
echo "=================================="

# Python check
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 is required." >&2; exit 1
fi

# Virtual environment
if [ ! -d "$ROOT/.venv" ]; then
  echo "[1/3] Creating virtual environment…"
  python3 -m venv "$ROOT/.venv"
fi

source "$ROOT/.venv/bin/activate"

echo "[2/3] Installing dependencies (first run may take a few minutes)…"
pip install --quiet --upgrade pip
pip install --quiet -r "$ROOT/requirements.txt"

echo "[3/3] Launching BeatStyle…"
cd "$ROOT"
python app.py
