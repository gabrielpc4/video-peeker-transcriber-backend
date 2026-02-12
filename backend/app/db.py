import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class Database:
    sqlite_path: str

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.sqlite_path)
        connection.row_factory = sqlite3.Row
        return connection


def initialize_database(database: Database) -> None:
    with database.connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
              item_id TEXT PRIMARY KEY,
              created_at_iso TEXT NOT NULL,
              source_type TEXT NOT NULL,
              source_url TEXT,
              local_media_path TEXT,

              title_text TEXT,

              transcription_status TEXT NOT NULL,
              enhanced_transcript_status TEXT NOT NULL,
              summary_status TEXT NOT NULL,
              breakdown_status TEXT NOT NULL,

              detected_language TEXT,
              transcript_text TEXT,
              enhanced_transcript_text TEXT,
              enhanced_transcript_error TEXT,
              summary_json TEXT,
              breakdown_json TEXT,

              last_error TEXT
            );
            """
        )

        existing_columns = connection.execute("PRAGMA table_info(items);").fetchall()
        existing_column_names = [row["name"] for row in existing_columns]

        if "title_text" not in existing_column_names:
            connection.execute("ALTER TABLE items ADD COLUMN title_text TEXT;")

        if "summary_status" not in existing_column_names:
            connection.execute("ALTER TABLE items ADD COLUMN summary_status TEXT NOT NULL DEFAULT 'pending';")

        if "summary_json" not in existing_column_names:
            connection.execute("ALTER TABLE items ADD COLUMN summary_json TEXT;")

        if "enhanced_transcript_status" not in existing_column_names:
            connection.execute("ALTER TABLE items ADD COLUMN enhanced_transcript_status TEXT NOT NULL DEFAULT 'pending';")

        if "enhanced_transcript_text" not in existing_column_names:
            connection.execute("ALTER TABLE items ADD COLUMN enhanced_transcript_text TEXT;")

        if "enhanced_transcript_error" not in existing_column_names:
            connection.execute("ALTER TABLE items ADD COLUMN enhanced_transcript_error TEXT;")

        connection.commit()

