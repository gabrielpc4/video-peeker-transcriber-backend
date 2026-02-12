import json
import os
import time

from .anthropic_client import AnthropicClient
from .assemblyai_client import AssemblyAiClient
from .downloader import download_with_ytdlp, extract_audio_with_ffmpeg
from .repository import ItemRepository


def _looks_like_video_file(local_path: str) -> bool:
    extension_text = os.path.splitext(local_path)[1].lower()
    return extension_text in [".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"]


def run_transcription_job(
    *,
    item_id: str,
    item_repository: ItemRepository,
    storage_dir: str,
    instagram_cookies_path: str,
    assemblyai_api_key: str,
    anthropic_api_key: str,
    extended_output: bool = False,
) -> None:
    record = item_repository.get_item(item_id)
    if record is None:
        raise RuntimeError("Item not found.")

    if record.transcription_status == "running":
        return

    item_repository.set_transcription_running(item_id)

    started_at = time.monotonic()

    def log_step(message: str) -> None:
        elapsed = time.monotonic() - started_at
        print(f"[transcribe:{item_id}] +{elapsed:0.2f}s {message}", flush=True)

    try:
        log_step(f"start source_type={record.source_type}")
        raw_media_path: str

        if record.source_type == "url":
            log_step("downloading media via yt-dlp")
            raw_media_path = download_with_ytdlp(
                source_url=record.source_url or "",
                output_dir=storage_dir,
                item_id=item_id,
                instagram_cookies_path=instagram_cookies_path,
            )
            try:
                size_bytes = os.path.getsize(raw_media_path)
                log_step(f"downloaded {raw_media_path} ({size_bytes} bytes)")
            except Exception:
                log_step(f"downloaded {raw_media_path}")
        else:
            if record.local_media_path is None:
                raise RuntimeError("Upload item missing local_media_path.")

            raw_media_path = record.local_media_path
            log_step(f"using uploaded media {raw_media_path}")

        extracted_audio_path: str

        if record.source_type == "upload":
            # Why: WhatsApp voice notes are already audio; keep max fidelity and save time.
            if _looks_like_video_file(raw_media_path):
                log_step("extracting audio from uploaded video via ffmpeg")
                extracted_audio_path = extract_audio_with_ffmpeg(
                    input_path=raw_media_path,
                    output_dir=storage_dir,
                    item_id=f"{item_id}-audio",
                )
            else:
                extracted_audio_path = raw_media_path
        else:
            # Why: diarization quality can drop a lot if we downmix to mono.
            # Still keep it relatively small (AAC 96k), but preserve stereo cues.
            log_step("extracting audio via ffmpeg (stereo, 96k)")
            extracted_audio_path = extract_audio_with_ffmpeg(
                input_path=raw_media_path,
                output_dir=storage_dir,
                item_id=f"{item_id}-audio",
                audio_channels="2",
                audio_sample_rate_hz="44100",
                audio_bitrate="96k",
            )

        assembly_client = AssemblyAiClient(api_key=assemblyai_api_key)
        log_step("uploading audio to AssemblyAI")
        upload_url = assembly_client.upload_file(extracted_audio_path)
        enable_speaker_labels = record.source_type == "url"
        log_step(f"creating transcript (speaker_labels={enable_speaker_labels})")
        transcript_id = assembly_client.create_transcript(upload_url, speaker_labels=enable_speaker_labels)
        log_step(f"polling transcript id={transcript_id}")
        transcript_result = assembly_client.poll_transcript(transcript_id)
        log_step("transcript completed")

        item_repository.set_transcription_completed(
            item_id=item_id,
            transcript_text=transcript_result.transcript_text,
            detected_language=transcript_result.detected_language_code,
        )

        if record.source_type == "url":
            try:
                item_repository.set_enhanced_transcript_running(item_id)

                anthropic_client = AnthropicClient(api_key=anthropic_api_key)
                log_step("enhancing transcript speakers via Claude")
                enhanced = anthropic_client.enhance_transcript_speakers(
                    transcript_text=transcript_result.transcript_text,
                    detected_language=transcript_result.detected_language_code,
                    extended_output=extended_output,
                )
                log_step("enhanced transcript completed")

                item_repository.set_enhanced_transcript_completed(
                    item_id=item_id,
                    enhanced_transcript_text=enhanced.enhancedTranscriptText,
                )
            except Exception as error:
                item_repository.set_enhanced_transcript_failed(item_id=item_id, error_message=str(error))
                log_step(f"enhanced transcript failed: {error}")
    except Exception as error:
        item_repository.set_transcription_failed(item_id=item_id, error_message=str(error))
        log_step(f"transcription failed: {error}")
        raise


def run_breakdown_job(*, item_id: str, item_repository: ItemRepository, anthropic_api_key: str, extended_output: bool = False) -> None:
    record = item_repository.get_item(item_id)
    if record is None:
        raise RuntimeError("Item not found.")

    if record.breakdown_status == "running":
        return

    transcript_text = (record.enhanced_transcript_text or "").strip() or (record.transcript_text or "").strip()
    if transcript_text == "":
        raise RuntimeError("Missing transcript_text. Run transcription first.")

    item_repository.set_breakdown_running(item_id)

    try:
        anthropic_client = AnthropicClient(api_key=anthropic_api_key)
        if record.source_type == "upload":
            recap = anthropic_client.generate_audio_recap(
                transcript_text=transcript_text,
                detected_language=record.detected_language,
                extended_output=extended_output,
            )

            breakdown_json = json.dumps(recap.__dict__, ensure_ascii=False, indent=2)
        else:
            breakdown = anthropic_client.generate_breakdown(
                transcript_text=transcript_text,
                detected_language=record.detected_language,
                extended_output=extended_output,
            )

            breakdown_json = json.dumps(breakdown.__dict__, ensure_ascii=False, indent=2)

        item_repository.set_breakdown_completed(item_id=item_id, breakdown_json=breakdown_json)
    except Exception as error:
        item_repository.set_breakdown_failed(item_id=item_id, error_message=str(error))
        raise


def run_summary_job(*, item_id: str, item_repository: ItemRepository, anthropic_api_key: str, extended_output: bool = False) -> None:
    record = item_repository.get_item(item_id)
    if record is None:
        raise RuntimeError("Item not found.")

    transcript_text = (record.enhanced_transcript_text or "").strip() or (record.transcript_text or "").strip()

    if record.source_type != "url":
        raise RuntimeError("Summary is only supported for URL items.")

    if record.summary_status == "running":
        return

    if transcript_text == "":
        item_repository.set_summary_failed(item_id=item_id, error_message="Missing transcript_text. Run transcription first.")
        raise RuntimeError("Missing transcript_text. Run transcription first.")

    item_repository.set_summary_running(item_id)

    try:
        anthropic_client = AnthropicClient(api_key=anthropic_api_key)
        summary = anthropic_client.generate_video_summary(
            transcript_text=transcript_text,
            detected_language=record.detected_language,
            extended_output=extended_output,
        )

        summary_json = json.dumps(summary.__dict__, ensure_ascii=False, indent=2)
        item_repository.set_summary_completed(item_id=item_id, summary_json=summary_json)
    except Exception as error:
        item_repository.set_summary_failed(item_id=item_id, error_message=str(error))
        raise

