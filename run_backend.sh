#!/usr/bin/env bash
set -euo pipefail

repo_root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$repo_root_dir"

if [[ -f "backend/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "backend/.env"
  set +a
fi

if ! command -v uvicorn >/dev/null 2>&1; then
  echo "uvicorn not found. Install backend dependencies first:"
  echo ""
  echo "  pip install -r backend/requirements.txt"
  echo ""
  exit 1
fi

exec uvicorn backend.app.main:app --reload --port 8000

