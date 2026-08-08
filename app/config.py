from pathlib import Path
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    assemblyai_api_key: str
    anthropic_api_key: str

    storage_dir: str
    sqlite_path: str

    instagram_cookies_path: str
    youtube_cookies_path: str


# Paths are resolved relative to the backend directory.
# Note: Using data/ so Render's persistent disk at /app/data is used.
STORAGE_DIR_RELATIVE = "data/storage"
SQLITE_PATH_RELATIVE = "data/video-transcriber.sqlite"
INSTAGRAM_COOKIES_PATH_RELATIVE = "secrets/instagram_cookies.txt"
YOUTUBE_COOKIES_PATH_RELATIVE = "secrets/youtube_cookies.txt"


def load_config() -> AppConfig:
    backend_directory = Path(__file__).resolve().parents[1]
    assemblyai_api_key = os.environ.get("ASSEMBLYAI_API_KEY", "").strip()
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()

    storage_dir = str((backend_directory / STORAGE_DIR_RELATIVE).resolve())
    sqlite_path = str((backend_directory / SQLITE_PATH_RELATIVE).resolve())
    instagram_cookies_path = str((backend_directory / INSTAGRAM_COOKIES_PATH_RELATIVE).resolve())
    youtube_cookies_path = str((backend_directory / YOUTUBE_COOKIES_PATH_RELATIVE).resolve())

    if assemblyai_api_key == "":
        raise RuntimeError("Missing ASSEMBLYAI_API_KEY environment variable.")

    if anthropic_api_key == "":
        raise RuntimeError("Missing ANTHROPIC_API_KEY environment variable.")

    return AppConfig(
        assemblyai_api_key=assemblyai_api_key,
        anthropic_api_key=anthropic_api_key,
        storage_dir=storage_dir,
        sqlite_path=sqlite_path,
        instagram_cookies_path=instagram_cookies_path,
        youtube_cookies_path=youtube_cookies_path,
    )

