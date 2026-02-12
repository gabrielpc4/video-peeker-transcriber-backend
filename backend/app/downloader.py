import os
import subprocess
import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadResult:
    downloaded_path: str
    extracted_audio_path: str


def ensure_directory_exists(directory_path: str) -> None:
    os.makedirs(directory_path, exist_ok=True)


def run_command(command_args: list[str]) -> None:
    if len(command_args) == 0:
        raise RuntimeError("Command is empty.")

    executable_name = command_args[0]
    resolved_executable = shutil.which(executable_name)
    if resolved_executable is None:
        raise RuntimeError(
            f"Missing dependency: '{executable_name}'.\n\n"
            "Install it and try again.\n\n"
            "macOS (Homebrew):\n"
            f"  brew install {executable_name}\n\n"
            "Or (pip):\n"
            f"  pip install {executable_name}\n"
        )

    command_text = " ".join(command_args)

    completed = subprocess.run(
        [resolved_executable] + command_args[1:],
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
    youtube_cookies_path: str,
) -> str:
    ensure_directory_exists(output_dir)

    output_template = os.path.join(output_dir, f"{item_id}.%(ext)s")

    is_instagram = "instagram.com" in source_url
    is_youtube = ("youtube.com" in source_url) or ("youtu.be" in source_url)

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

    # YouTube now often requires a JS runtime to solve "n" challenges / signature logic.
    # If node is available, allow yt-dlp to use it.
    if is_youtube and shutil.which("node") is not None:
        command_args.extend(["--js-runtimes", "node"])

    # Only use Instagram cookies for Instagram URLs.
    # Also, yt-dlp may try to save cookies back to the provided jar path. To avoid
    # write errors (e.g. read-only mounts) and avoid mutating the source file,
    # we pass a per-item copy stored in output_dir (writable).
    if is_youtube and os.path.exists(youtube_cookies_path):
        cookie_jar_copy_path = os.path.join(output_dir, f"{item_id}-cookies-youtube.txt")
        shutil.copyfile(youtube_cookies_path, cookie_jar_copy_path)
        command_args.extend(["--cookies", cookie_jar_copy_path])
    elif is_instagram and os.path.exists(instagram_cookies_path):
        cookie_jar_copy_path = os.path.join(output_dir, f"{item_id}-cookies.txt")
        shutil.copyfile(instagram_cookies_path, cookie_jar_copy_path)
        command_args.extend(["--cookies", cookie_jar_copy_path])
    elif is_instagram:
        # Local dev fallback (requires Chrome on host).
        command_args.extend(["--cookies-from-browser", "chrome"])

    command_args.append(source_url)

    try:
        run_command(command_args)
    except Exception as first_error:
        # If Instagram download fails but we are on a dev machine with Chrome logged in,
        # retry using cookies from browser (even if the file exists but is stale).
        if is_instagram:
            retry_args = [arg for arg in command_args if arg not in ["--cookies", instagram_cookies_path]]
            retry_args = [arg for arg in retry_args if arg != "--cookies-from-browser"]
            # Ensure "--cookies-from-browser chrome" is present.
            if "--cookies-from-browser" not in retry_args:
                retry_args.insert(len(retry_args) - 1, "--cookies-from-browser")
                retry_args.insert(len(retry_args) - 1, "chrome")
            try:
                run_command(retry_args)
            except Exception:
                raise first_error
        else:
            raise

    matching_files: list[str] = []
    for filename in os.listdir(output_dir):
        if filename.startswith(f"{item_id}."):
            matching_files.append(os.path.join(output_dir, filename))

    if len(matching_files) == 0:
        raise RuntimeError("yt-dlp did not produce any file.")

    matching_files.sort(key=lambda p: os.path.getsize(p), reverse=True)
    return matching_files[0]


def extract_audio_with_ffmpeg(
    *,
    input_path: str,
    output_dir: str,
    item_id: str,
    audio_channels: str = "1",
    audio_sample_rate_hz: str = "16000",
    audio_bitrate: str = "48k",
) -> str:
    ensure_directory_exists(output_dir)

    output_path = os.path.join(output_dir, f"{item_id}.m4a")

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

