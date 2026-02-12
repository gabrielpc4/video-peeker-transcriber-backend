#!/usr/bin/env bash
set -euo pipefail

# Exports Instagram cookies from the local Chrome profile into a Netscape cookies.txt file.
# This file is intentionally gitignored (backend/secrets/).
#
# Requirements:
# - yt-dlp installed and available in PATH
#
# Notes:
# - This reads cookies from your local Chrome profile. Do NOT commit the output file.
# - On macOS you may be prompted for permission because Chrome cookies are protected.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
BACKEND_DIR="$(cd -- "$SCRIPT_DIR/.." &>/dev/null && pwd)"

OUT_DIR="$BACKEND_DIR/secrets"
OUT_PATH="$OUT_DIR/instagram_cookies.txt"

mkdir -p "$OUT_DIR"

command -v yt-dlp >/dev/null || {
  echo "Missing dependency: yt-dlp"
  echo "Install with: brew install yt-dlp"
  exit 1
}

echo "Exporting cookies to: $OUT_PATH"
yt-dlp --cookies-from-browser chrome --cookies "$OUT_PATH" "https://www.instagram.com/"
echo "Done."
echo "Keep this file private. It is gitignored at backend/secrets/."

