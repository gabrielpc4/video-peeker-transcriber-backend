import os
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadResult:
    downloaded_path: str
    extracted_audio_path: str


def ensure_directory_exists(directory_path: str) -> None:
    os.makedirs(directory_path, exist_ok=True)


def run_command(command_args: list[str]) -> None:
    command_text = " ".join(command_args)

    completed = subprocess.run(
        command_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if completed.returncode != 0:
        raise RuntimeError(f"Command failed ({completed.returncode}): {command_text}\n\n{completed.stdout}")


def download_with_ytdlp(
    *,
    source_url: str,
    output_dir: str,
    item_id: str,
    instagram_cookies_path: str,
) -> str:
    ensure_directory_exists(output_dir)

    output_template = os.path.join(output_dir, f"{item_id}.%(ext)s")

    if "instagram.com" in source_url and os.path.exists(instagram_cookies_path) is False:
        raise RuntimeError(
            "Instagram link requires cookies for reliable access. "
            "Export cookies (Netscape format) to backend/secrets/instagram_cookies.txt."
        )

    # Why: for social/video links, we optimize for speed and smaller downloads.
    # Prefer a lower-bitrate audio stream when available.
    format_selector = "bestaudio[abr<=64]/bestaudio[abr<=96]/bestaudio/best"

    command_args = [
        "yt-dlp",
        "--no-playlist",
        "-f",
        format_selector,
        "-o",
        output_template,
    ]

    if os.path.exists(instagram_cookies_path):
        command_args.extend(["--cookies", instagram_cookies_path])

    command_args.append(source_url)

    run_command(command_args)

    matching_files: list[str] = []
    for filename in os.listdir(output_dir):
        if filename.startswith(f"{item_id}."):
            matching_files.append(os.path.join(output_dir, filename))

    if len(matching_files) == 0:
        raise RuntimeError("yt-dlp did not produce any file.")

    matching_files.sort(key=lambda p: os.path.getsize(p), reverse=True)
    return matching_files[0]


def extract_audio_with_ffmpeg(*, input_path: str, output_dir: str, item_id: str) -> str:
    ensure_directory_exists(output_dir)

    output_path = os.path.join(output_dir, f"{item_id}.m4a")

    # Why: speech transcription does not benefit from stereo; mono is smaller and faster.
    audio_channels = "1"
    audio_sample_rate_hz = "16000"
    audio_bitrate = "48k"

    command_args = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vn",
        "-ac",
        audio_channels,
        "-ar",
        audio_sample_rate_hz,
        "-c:a",
        "aac",
        "-b:a",
        audio_bitrate,
        output_path,
    ]

    run_command(command_args)

    if os.path.exists(output_path) is False:
        raise RuntimeError("ffmpeg did not produce audio output.")

    return output_path

