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

              transcription_status TEXT NOT NULL,
              breakdown_status TEXT NOT NULL,

              detected_language TEXT,
              transcript_text TEXT,
              breakdown_json TEXT,

              last_error TEXT
            );
            """
        )

        connection.commit()

