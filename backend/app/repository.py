import json
import uuid
from dataclasses import dataclass
from typing import Optional

from .db import Database
from .models import ItemResponse, now_iso


@dataclass(frozen=True)
class ItemRecord:
    item_id: str
    created_at_iso: str
    source_type: str
    source_url: Optional[str]
    local_media_path: Optional[str]

    title_text: Optional[str]

    transcription_status: str
    enhanced_transcript_status: str
    summary_status: str
    breakdown_status: str

    detected_language: Optional[str]
    transcript_text: Optional[str]
    enhanced_transcript_text: Optional[str]
    enhanced_transcript_error: Optional[str]
    summary_json: Optional[str]
    breakdown_json: Optional[str]

    last_error: Optional[str]


class ItemRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def create_url_item(self, source_url: str, title_text: str | None) -> str:
        item_id = str(uuid.uuid4())
        created_at_iso = now_iso()

        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT INTO items (
                  item_id, created_at_iso, source_type, source_url, local_media_path,
                  title_text,
                  transcription_status, enhanced_transcript_status, summary_status, breakdown_status,
                  detected_language, transcript_text, enhanced_transcript_text, enhanced_transcript_error, summary_json, breakdown_json,
                  last_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    created_at_iso,
                    "url",
                    source_url,
                    None,
                    title_text,
                    "pending",
                    "pending",
                    "pending",
                    "pending",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            )
            connection.commit()

        return item_id

    def create_upload_item(self, local_media_path: str) -> str:
        item_id = str(uuid.uuid4())
        created_at_iso = now_iso()

        with self._database.connect() as connection:
            connection.execute(
                """
                INSERT INTO items (
                  item_id, created_at_iso, source_type, source_url, local_media_path,
                  title_text,
                  transcription_status, enhanced_transcript_status, summary_status, breakdown_status,
                  detected_language, transcript_text, enhanced_transcript_text, enhanced_transcript_error, summary_json, breakdown_json,
                  last_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    created_at_iso,
                    "upload",
                    None,
                    local_media_path,
                    None,
                    "pending",
                    "pending",
                    "pending",
                    "pending",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            )
            connection.commit()

        return item_id

    def get_item(self, item_id: str) -> ItemRecord | None:
        with self._database.connect() as connection:
            row = connection.execute("SELECT * FROM items WHERE item_id = ?", (item_id,)).fetchone()

        if row is None:
            return None

        return ItemRecord(
            item_id=row["item_id"],
            created_at_iso=row["created_at_iso"],
            source_type=row["source_type"],
            source_url=row["source_url"],
            local_media_path=row["local_media_path"],
            title_text=row["title_text"],
            transcription_status=row["transcription_status"],
            enhanced_transcript_status=row["enhanced_transcript_status"],
            summary_status=row["summary_status"],
            breakdown_status=row["breakdown_status"],
            detected_language=row["detected_language"],
            transcript_text=row["transcript_text"],
            enhanced_transcript_text=row["enhanced_transcript_text"],
            enhanced_transcript_error=row["enhanced_transcript_error"],
            summary_json=row["summary_json"],
            breakdown_json=row["breakdown_json"],
            last_error=row["last_error"],
        )

    def set_transcription_running(self, item_id: str) -> None:
        self._update(item_id=item_id, updates={"transcription_status": "running", "last_error": None})

    def set_transcription_completed(self, *, item_id: str, transcript_text: str, detected_language: str | None) -> None:
        self._update(
            item_id=item_id,
            updates={
                "transcription_status": "completed",
                "transcript_text": transcript_text,
                "detected_language": detected_language,
                "last_error": None,
            },
        )

    def set_transcription_failed(self, *, item_id: str, error_message: str) -> None:
        self._update(item_id=item_id, updates={"transcription_status": "failed", "last_error": error_message})

    def set_enhanced_transcript_running(self, item_id: str) -> None:
        self._update(
            item_id=item_id,
            updates={
                "enhanced_transcript_status": "running",
                "enhanced_transcript_error": None,
            },
        )

    def set_enhanced_transcript_completed(self, *, item_id: str, enhanced_transcript_text: str) -> None:
        self._update(
            item_id=item_id,
            updates={
                "enhanced_transcript_status": "completed",
                "enhanced_transcript_text": enhanced_transcript_text,
                "enhanced_transcript_error": None,
            },
        )

    def set_enhanced_transcript_failed(self, *, item_id: str, error_message: str) -> None:
        self._update(
            item_id=item_id,
            updates={
                "enhanced_transcript_status": "failed",
                "enhanced_transcript_error": error_message,
            },
        )

    def set_summary_running(self, item_id: str) -> None:
        self._update(item_id=item_id, updates={"summary_status": "running", "last_error": None})

    def set_summary_completed(self, *, item_id: str, summary_json: str) -> None:
        self._update(item_id=item_id, updates={"summary_status": "completed", "summary_json": summary_json, "last_error": None})

    def set_summary_failed(self, *, item_id: str, error_message: str) -> None:
        self._update(item_id=item_id, updates={"summary_status": "failed", "last_error": error_message})

    def set_breakdown_running(self, item_id: str) -> None:
        self._update(item_id=item_id, updates={"breakdown_status": "running", "last_error": None})

    def set_breakdown_completed(self, *, item_id: str, breakdown_json: str) -> None:
        self._update(item_id=item_id, updates={"breakdown_status": "completed", "breakdown_json": breakdown_json, "last_error": None})

    def set_breakdown_failed(self, *, item_id: str, error_message: str) -> None:
        self._update(item_id=item_id, updates={"breakdown_status": "failed", "last_error": error_message})

    def to_response(self, record: ItemRecord) -> ItemResponse:
        return ItemResponse(
            item_id=record.item_id,
            created_at_iso=record.created_at_iso,
            source_type=record.source_type,
            source_url=record.source_url,
            title_text=record.title_text,
            transcription_status=record.transcription_status,
            enhanced_transcript_status=record.enhanced_transcript_status,
            summary_status=record.summary_status,
            breakdown_status=record.breakdown_status,
            detected_language=record.detected_language,
            transcript_text=record.transcript_text,
            enhanced_transcript_text=record.enhanced_transcript_text,
            enhanced_transcript_error=record.enhanced_transcript_error,
            summary_json=record.summary_json,
            breakdown_json=record.breakdown_json,
            last_error=record.last_error,
        )

    def _update(self, *, item_id: str, updates: dict) -> None:
        if len(updates) == 0:
            return

        columns = []
        values = []

        for key, value in updates.items():
            columns.append(f"{key} = ?")
            values.append(value)

        values.append(item_id)

        query_text = f"UPDATE items SET {', '.join(columns)} WHERE item_id = ?"

        with self._database.connect() as connection:
            connection.execute(query_text, values)
            connection.commit()

