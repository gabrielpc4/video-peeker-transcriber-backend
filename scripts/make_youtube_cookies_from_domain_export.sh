#!/usr/bin/env bash
set -euo pipefail

# Convert a Cookie-Editor style domain export file into a yt-dlp compatible
# Netscape cookies.txt for YouTube.
#
# Input (expected):
# - backend/secrets/www.youtube.com
#
# Output:
# - backend/secrets/youtube_cookies.txt
#
# Notes:
# - The input format is the tab-separated export some browser extensions produce:
#   name <tab> value <tab> domain <tab> path <tab> expires(ISO/Session) <tab> ...
# - This script keeps all non-expired cookies for YouTube/Google domains and
#   writes them in Netscape format.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
BACKEND_DIR="$(cd -- "$SCRIPT_DIR/.." &>/dev/null && pwd)"

SECRETS_DIR="$BACKEND_DIR/secrets"
IN_PATH="$SECRETS_DIR/www.youtube.com"
OUT_PATH="$SECRETS_DIR/youtube_cookies.txt"

mkdir -p "$SECRETS_DIR"

if [[ ! -f "$IN_PATH" ]]; then
  echo "Missing input file at: $IN_PATH"
  echo "Export cookies for https://www.youtube.com to that file and re-run."
  exit 1
fi

echo "Generating yt-dlp cookie jar: $OUT_PATH"
PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
  if [[ -x "$HOME/miniconda3/bin/python" ]]; then
    PYTHON_BIN="$HOME/miniconda3/bin/python"
  else
    PYTHON_BIN="$(command -v python3 || true)"
    if [[ -z "${PYTHON_BIN}" ]]; then
      PYTHON_BIN="$(command -v python || true)"
    fi
  fi
fi

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "Could not find python. Install Python or Miniconda at ~/miniconda3."
  exit 1
fi

"$PYTHON_BIN" "$BACKEND_DIR/scripts/make_youtube_cookies_from_domain_export.py" --in "$IN_PATH" --out "$OUT_PATH"
echo "Done."

