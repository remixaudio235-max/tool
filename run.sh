#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"

echo "==================================="
echo "   BeatShift – Music Beat Converter"
echo "==================================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 is required." >&2
  exit 1
fi

# Create virtual environment if needed
if [ ! -d "$ROOT/.venv" ]; then
  echo "[1/3] Creating virtual environment..."
  python3 -m venv "$ROOT/.venv"
fi

# Activate
source "$ROOT/.venv/bin/activate"

# Install dependencies
echo "[2/3] Installing dependencies (this may take a minute on first run)..."
pip install --quiet --upgrade pip
pip install --quiet -r "$ROOT/requirements.txt"

# Launch server
echo "[3/3] Starting server at http://localhost:8000 ..."
echo ""
echo "  Open your browser at: http://localhost:8000"
echo "  Press Ctrl+C to stop."
echo ""

cd "$BACKEND"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
