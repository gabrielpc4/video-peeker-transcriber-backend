import json
import os

from .anthropic_client import AnthropicClient
from .assemblyai_client import AssemblyAiClient
from .downloader import download_with_ytdlp, extract_audio_with_ffmpeg
from .repository import ItemRepository


def _looks_like_video_file(local_path: str) -> bool:
    extension_text = os.path.splitext(local_path)[1].lower()
    return extension_text in [".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"]


def run_transcription_job(*, item_id: str, item_repository: ItemRepository, storage_dir: str, instagram_cookies_path: str, assemblyai_api_key: str) -> None:
    record = item_repository.get_item(item_id)
    if record is None:
        raise RuntimeError("Item not found.")

    if record.transcription_status == "running":
        return

    item_repository.set_transcription_running(item_id)

    try:
        raw_media_path: str

        if record.source_type == "url":
            raw_media_path = download_with_ytdlp(
                source_url=record.source_url or "",
                output_dir=storage_dir,
                item_id=item_id,
                instagram_cookies_path=instagram_cookies_path,
            )
        else:
            if record.local_media_path is None:
                raise RuntimeError("Upload item missing local_media_path.")

            raw_media_path = record.local_media_path

        extracted_audio_path: str

        if record.source_type == "upload":
            # Why: WhatsApp voice notes are already audio; keep max fidelity and save time.
            if _looks_like_video_file(raw_media_path):
                extracted_audio_path = extract_audio_with_ffmpeg(
                    input_path=raw_media_path,
                    output_dir=storage_dir,
                    item_id=f"{item_id}-audio",
                )
            else:
                extracted_audio_path = raw_media_path
        else:
            # URL sources are optimized for speed (smaller audio).
            extracted_audio_path = extract_audio_with_ffmpeg(
                input_path=raw_media_path,
                output_dir=storage_dir,
                item_id=f"{item_id}-audio",
            )

        assembly_client = AssemblyAiClient(api_key=assemblyai_api_key)
        upload_url = assembly_client.upload_file(extracted_audio_path)
        transcript_id = assembly_client.create_transcript(upload_url)
        transcript_result = assembly_client.poll_transcript(transcript_id)

        item_repository.set_transcription_completed(
            item_id=item_id,
            transcript_text=transcript_result.transcript_text,
            detected_language=transcript_result.detected_language_code,
        )
    except Exception as error:
        item_repository.set_transcription_failed(item_id=item_id, error_message=str(error))
        raise


def run_breakdown_job(*, item_id: str, item_repository: ItemRepository, anthropic_api_key: str) -> None:
    record = item_repository.get_item(item_id)
    if record is None:
        raise RuntimeError("Item not found.")

    if record.breakdown_status == "running":
        return

    transcript_text = (record.transcript_text or "").strip()
    if transcript_text == "":
        raise RuntimeError("Missing transcript_text. Run transcription first.")

    item_repository.set_breakdown_running(item_id)

    try:
        anthropic_client = AnthropicClient(api_key=anthropic_api_key)
        if record.source_type == "upload":
            recap = anthropic_client.generate_audio_recap(
                transcript_text=transcript_text,
                detected_language=record.detected_language,
            )

            breakdown_json = json.dumps(recap.__dict__, ensure_ascii=False, indent=2)
        else:
            breakdown = anthropic_client.generate_breakdown(
                transcript_text=transcript_text,
                detected_language=record.detected_language,
            )

            breakdown_json = json.dumps(breakdown.__dict__, ensure_ascii=False, indent=2)

        item_repository.set_breakdown_completed(item_id=item_id, breakdown_json=breakdown_json)
    except Exception as error:
        item_repository.set_breakdown_failed(item_id=item_id, error_message=str(error))
        raise

