#!/usr/bin/env bash
set -euo pipefail

# This script no longer tries to "export cookies via yt-dlp" (yt-dlp doesn't write cookies.txt).
# Instead, it trims an existing Netscape cookies.txt to the minimal set of Instagram/Facebook
# domains we need.
#
# Requirements:
# - python available
#
# Notes:
# - Do NOT commit the output file.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
BACKEND_DIR="$(cd -- "$SCRIPT_DIR/.." &>/dev/null && pwd)"

OUT_DIR="$BACKEND_DIR/secrets"
OUT_PATH="$OUT_DIR/instagram_cookies.txt"

mkdir -p "$OUT_DIR"

if [[ ! -f "$OUT_PATH" ]]; then
  echo "Missing cookies file at: $OUT_PATH"
  echo "Create it in Netscape format (cookies.txt) and re-run this script to trim it."
  exit 1
fi

echo "Trimming cookies in-place: $OUT_PATH"
python "$BACKEND_DIR/scripts/trim_instagram_cookies_txt.py" --in "$OUT_PATH" --out "$OUT_PATH" --in-place
echo "Done. Backup saved as: $OUT_PATH.bak"
echo "Keep this file private. It is gitignored at backend/secrets/."

