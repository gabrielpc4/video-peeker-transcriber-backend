#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f ".env" ]]; then
  echo "Missing .env at: $SCRIPT_DIR/.env"
  echo "Create it based on .env.example"
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
  if [[ -x "$HOME/miniconda3/bin/python" ]]; then
    PYTHON_BIN="$HOME/miniconda3/bin/python"
  else
    PYTHON_BIN="$(command -v python || true)"
  fi
fi

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "Could not find python. Install Python or Miniconda at ~/miniconda3."
  exit 1
fi

echo "Using python: $PYTHON_BIN"

if ! "$PYTHON_BIN" -m pip install -r requirements.txt; then
  echo
  echo "pip install failed. If you're using a Homebrew-managed python, you may hit PEP 668."
  echo "Recommended fix: install/use Miniconda at ~/miniconda3, or set PYTHON_BIN to your conda python."
  echo
  exit 1
fi

exec "$PYTHON_BIN" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

