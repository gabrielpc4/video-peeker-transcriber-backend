import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    assemblyai_api_key: str
    anthropic_api_key: str

    storage_dir: str
    sqlite_path: str

    instagram_cookies_path: str


def load_config() -> AppConfig:
    assemblyai_api_key = os.getenv("ASSEMBLYAI_API_KEY", "").strip()
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    storage_dir = os.getenv("STORAGE_DIR", "backend/storage").strip()
    sqlite_path = os.getenv("SQLITE_PATH", "backend/viberecap.sqlite").strip()

    instagram_cookies_path = os.getenv("INSTAGRAM_COOKIES_PATH", "backend/secrets/instagram_cookies.txt").strip()

    if assemblyai_api_key == "":
        raise RuntimeError("Missing ASSEMBLYAI_API_KEY in environment.")

    if anthropic_api_key == "":
        raise RuntimeError("Missing ANTHROPIC_API_KEY in environment.")

    return AppConfig(
        assemblyai_api_key=assemblyai_api_key,
        anthropic_api_key=anthropic_api_key,
        storage_dir=storage_dir,
        sqlite_path=sqlite_path,
        instagram_cookies_path=instagram_cookies_path,
    )

