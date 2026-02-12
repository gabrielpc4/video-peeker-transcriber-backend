from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


SourceType = Literal["url", "upload"]
JobStatus = Literal["pending", "running", "completed", "failed"]


class CreateUrlItemRequest(BaseModel):
    source_url: str = Field(min_length=4)


class CreateItemResponse(BaseModel):
    item_id: str


class ItemResponse(BaseModel):
    item_id: str
    created_at_iso: str
    source_type: SourceType
    source_url: Optional[str]

    title_text: Optional[str]

    transcription_status: JobStatus
    enhanced_transcript_status: JobStatus
    summary_status: JobStatus
    breakdown_status: JobStatus

    detected_language: Optional[str]
    transcript_text: Optional[str]
    enhanced_transcript_text: Optional[str]
    enhanced_transcript_error: Optional[str]
    summary_json: Optional[str]
    breakdown_json: Optional[str]

    last_error: Optional[str]


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

