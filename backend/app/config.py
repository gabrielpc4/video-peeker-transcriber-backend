import os
from pathlib import Path
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    assemblyai_api_key: str
    anthropic_api_key: str

    storage_dir: str
    sqlite_path: str

    instagram_cookies_path: str


def _resolve_path_relative_to_backend_dir(backend_directory: Path, raw_value: str) -> str:
    trimmed = raw_value.strip()
    if trimmed == "":
        return str(backend_directory)

    candidate = Path(trimmed)
    if candidate.is_absolute():
        return str(candidate)

    # If user passes "backend/..." we treat it as relative to the repo root (parent of backend/).
    # Otherwise treat it as relative to the backend/ directory.
    if trimmed.startswith("backend/") or trimmed.startswith("backend\\"):
        return str((backend_directory.parent / candidate).resolve())

    return str((backend_directory / candidate).resolve())


def load_config() -> AppConfig:
    backend_directory = Path(__file__).resolve().parents[1]
    dotenv_path = backend_directory / ".env"

    load_dotenv(dotenv_path=dotenv_path, override=False)

    assemblyai_api_key = os.getenv("ASSEMBLYAI_API_KEY", "").strip()
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    default_storage_dir = str((backend_directory / "storage").resolve())
    default_sqlite_path = str((backend_directory / "videopeek.sqlite").resolve())

    storage_dir = _resolve_path_relative_to_backend_dir(backend_directory, os.getenv("STORAGE_DIR", default_storage_dir))
    sqlite_path = _resolve_path_relative_to_backend_dir(backend_directory, os.getenv("SQLITE_PATH", default_sqlite_path))

    default_instagram_cookies_path = str((backend_directory / "secrets" / "instagram_cookies.txt").resolve())
    instagram_cookies_path = _resolve_path_relative_to_backend_dir(
        backend_directory, os.getenv("INSTAGRAM_COOKIES_PATH", default_instagram_cookies_path)
    )

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

