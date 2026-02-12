#!/usr/bin/env python3
"""
Inspect items table: print item_id, source_type, status columns, and transcript lengths.
Use the same Python env as the backend (e.g. venv with pip install -r backend/requirements.txt).

From project root (VibeRecap):
  PYTHONPATH=. python backend/scripts/inspect_db.py
  or:  python -m backend.scripts.inspect_db
"""
import sys
from pathlib import Path

# Project root = parent of backend/
backend_dir = Path(__file__).resolve().parents[1]
repo_root = backend_dir.parent
sys.path.insert(0, str(repo_root))

from backend.app.config import load_config
from backend.app.db import Database

def main():
    config = load_config()
    db = Database(sqlite_path=config.sqlite_path)

    with db.connect() as conn:
        rows = conn.execute(
            """
            SELECT
                item_id,
                source_type,
                transcription_status,
                enhanced_transcript_status,
                summary_status,
                breakdown_status,
                length(trim(coalesce(transcript_text, ''))) AS transcript_len,
                length(trim(coalesce(enhanced_transcript_text, ''))) AS enhanced_len
            FROM items
            ORDER BY created_at_iso DESC
            LIMIT 20
            """
        ).fetchall()

    if not rows:
        print("No rows in items table.")
        return

    print("item_id (full) | source_type | transcr | enhanced | summary | breakdown | transcript_len | enhanced_len")
    print("-" * 100)
    for row in rows:
        print(
            row["item_id"],
            row["source_type"],
            row["transcription_status"],
            row["enhanced_transcript_status"],
            row["summary_status"],
            row["breakdown_status"],
            row["transcript_len"],
            row["enhanced_len"],
            sep=" | ",
        )


if __name__ == "__main__":
    main()
