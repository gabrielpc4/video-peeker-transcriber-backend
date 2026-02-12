#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f ".env" ]]; then
  echo "Missing .env at: $SCRIPT_DIR/.env"
  echo "Create it based on .env.example"
  exit 1
fi

python -m pip install -r requirements.txt

exec python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

