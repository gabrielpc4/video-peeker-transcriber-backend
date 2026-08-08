import os
import uuid
import datetime as dt
import subprocess
import shutil
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import AppConfig, load_config
from .db import Database, initialize_database
from .metadata import try_resolve_title
from .models import (
    CreateItemResponse,
    CreateUrlItemRequest,
    DeviceCookie,
    ItemResponse,
    UploadYoutubeCookiesRequest,
    UploadYoutubeCookiesResponse,
)
from .repository import ItemRepository
from .tasks import run_breakdown_job, run_summary_job, run_transcription_job


def _is_allowed_youtube_cookie_domain(domain: str) -> bool:
    normalized = domain.lower().lstrip(".")
    return (
        normalized == "youtube.com"
        or normalized.endswith(".youtube.com")
        or normalized == "google.com"
        or normalized.endswith(".google.com")
        or normalized == "googlevideo.com"
        or normalized.endswith(".googlevideo.com")
        or normalized == "ytimg.com"
        or normalized.endswith(".ytimg.com")
    )


def _format_device_cookie_to_netscape(cookie: DeviceCookie) -> str:
    include_subdomains = "TRUE" if cookie.domain.startswith(".") else "FALSE"
    secure = "TRUE" if cookie.secure else "FALSE"
    expires_epoch = 0 if (cookie.session_only or cookie.expires_epoch is None) else max(0, int(cookie.expires_epoch))
    domain_out = cookie.domain
    if cookie.http_only:
        domain_out = "#HttpOnly_" + domain_out
    return "\t".join(
        [
            domain_out,
            include_subdomains,
            cookie.path or "/",
            secure,
            str(expires_epoch),
            cookie.name,
            cookie.value,
        ]
    )


def create_app() -> FastAPI:
    app = FastAPI(title="Video Peeker Transcriber Backend")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    config = load_config()
    database = Database(sqlite_path=config.sqlite_path)
    initialize_database(database)

    item_repository = ItemRepository(database)

    os.makedirs(config.storage_dir, exist_ok=True)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/debug/youtube-cookies")
    def debug_youtube_cookies() -> dict[str, object]:
        """
        Returns the exact cookie jar file contents used for YouTube downloads.

        WARNING: This endpoint intentionally exposes sensitive cookies. This is a
        private tool by explicit user request.
        """
        path = config.youtube_cookies_path
        exists = os.path.exists(path)
        size_bytes: int | None = None
        mtime_iso: str | None = None
        content: str | None = None
        error_message: str | None = None

        if exists:
            try:
                stat = os.stat(path)
                size_bytes = int(stat.st_size)
                mtime_iso = dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc).isoformat()
                content = open(path, "r", encoding="utf-8", errors="replace").read()
            except Exception as error:
                error_message = str(error)

        return {
            "path": path,
            "exists": exists,
            "size_bytes": size_bytes,
            "mtime_iso": mtime_iso,
            "storage_dir": config.storage_dir,
            "content": content,
            "error": error_message,
        }

    @app.post("/youtube-cookies/upload", response_model=UploadYoutubeCookiesResponse)
    def upload_youtube_cookies(request: UploadYoutubeCookiesRequest) -> UploadYoutubeCookiesResponse:
        deduped_by_key: dict[tuple[str, str, str], DeviceCookie] = {}
        for cookie in request.cookies:
            if cookie.name.strip() == "" or cookie.domain.strip() == "":
                continue
            if _is_allowed_youtube_cookie_domain(cookie.domain) is False:
                continue
            key = (cookie.domain.lower(), cookie.path or "/", cookie.name)
            deduped_by_key[key] = cookie

        kept_cookies = list(deduped_by_key.values())

        if len(kept_cookies) == 0:
            raise HTTPException(status_code=400, detail="No YouTube/Google cookies found in payload.")

        lines: list[str] = []
        lines.append("# Netscape HTTP Cookie File\n")
        lines.append("# Uploaded from Video Transcriber mobile session\n")
        lines.append("# This file is used by yt-dlp via --cookies\n")
        lines.append("\n")

        rendered_cookie_lines = [_format_device_cookie_to_netscape(cookie) for cookie in kept_cookies]
        rendered_cookie_lines.sort(key=lambda line: line.split("\t")[0].lstrip("#HttpOnly_").lstrip(".").lower() + "\t" + line)
        for cookie_line in rendered_cookie_lines:
            lines.append(cookie_line + "\n")

        output_path = config.youtube_cookies_path
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write("".join(lines))

        stat = os.stat(output_path)
        mtime_iso = dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc).isoformat()
        return UploadYoutubeCookiesResponse(
            path=output_path,
            written_count=len(request.cookies),
            kept_count=len(kept_cookies),
            dropped_count=len(request.cookies) - len(kept_cookies),
            mtime_iso=mtime_iso,
        )

    @app.get("/debug/ytdlp")
    def debug_ytdlp() -> dict[str, object]:
        """
        Debug info for yt-dlp EJS runtime setup.

        WARNING: This endpoint is for private debugging only.
        """

        def which(name: str) -> str | None:
            try:
                return shutil.which(name)
            except Exception:
                return None

        def run_version(cmd: list[str]) -> str | None:
            try:
                completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=10)
                return (completed.stdout or "").strip()
            except Exception as error:
                return f"error: {error}"

        return {
            "yt_dlp_path": which("yt-dlp"),
            "yt_dlp_version": run_version(["yt-dlp", "--version"]) if which("yt-dlp") else None,
            "deno_path": which("deno"),
            "deno_version": run_version(["deno", "--version"]) if which("deno") else None,
            "node_path": which("node"),
            "node_version": run_version(["node", "--version"]) if which("node") else None,
            "path_env": os.getenv("PATH"),
        }

    @app.post("/items", response_model=CreateItemResponse)
    def create_url_item(request: CreateUrlItemRequest) -> CreateItemResponse:
        source_url = request.source_url.strip()
        if source_url == "":
            raise HTTPException(status_code=400, detail="source_url is empty.")

        if source_url.startswith("file://"):
            raise HTTPException(status_code=400, detail="file:// URLs are not supported. Upload the audio instead.")

        title_text = try_resolve_title(source_url)
        item_id = item_repository.create_url_item(source_url=source_url, title_text=title_text)
        return CreateItemResponse(item_id=item_id)

    @app.post("/items/upload", response_model=CreateItemResponse)
    async def create_upload_item(file: UploadFile = File(...)) -> CreateItemResponse:
        if file.filename is None or file.filename.strip() == "":
            raise HTTPException(status_code=400, detail="Missing filename.")

        content = await file.read()
        if content is None or len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty upload.")

        safe_extension = os.path.splitext(file.filename)[1]
        if safe_extension == "":
            safe_extension = ".bin"

        item_id = str(uuid.uuid4())
        temporary_path = os.path.join(config.storage_dir, f"{item_id}-upload{safe_extension}")
        with open(temporary_path, "wb") as output_handle:
            output_handle.write(content)

        item_repository.create_upload_item_with_id(item_id=item_id, local_media_path=temporary_path)
        return CreateItemResponse(item_id=item_id)

    @app.post("/items/{item_id}/transcribe", response_model=ItemResponse)
    def transcribe_item(
        item_id: str,
        background_tasks: BackgroundTasks,
        extended_output: bool = False,
    ) -> ItemResponse:
        record = item_repository.get_item(item_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Item not found.")

        background_tasks.add_task(
            run_transcription_job,
            item_id=item_id,
            item_repository=item_repository,
            storage_dir=config.storage_dir,
            instagram_cookies_path=config.instagram_cookies_path,
                youtube_cookies_path=config.youtube_cookies_path,
            assemblyai_api_key=config.assemblyai_api_key,
            anthropic_api_key=config.anthropic_api_key,
            extended_output=extended_output,
        )

        latest_record = item_repository.get_item(item_id)
        if latest_record is None:
            raise HTTPException(status_code=404, detail="Item not found.")

        return item_repository.to_response(latest_record)

    @app.post("/items/{item_id}/breakdown", response_model=ItemResponse)
    def breakdown_item(
        item_id: str,
        background_tasks: BackgroundTasks,
        extended_output: bool = False,
    ) -> ItemResponse:
        record = item_repository.get_item(item_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Item not found.")

        transcript_for_breakdown = (record.enhanced_transcript_text or "").strip() or (record.transcript_text or "").strip()
        if transcript_for_breakdown == "":
            raise HTTPException(status_code=400, detail="Missing transcript_text. Run transcription first.")

        background_tasks.add_task(
            run_breakdown_job,
            item_id=item_id,
            item_repository=item_repository,
            anthropic_api_key=config.anthropic_api_key,
            extended_output=extended_output,
        )

        latest_record = item_repository.get_item(item_id)
        if latest_record is None:
            raise HTTPException(status_code=404, detail="Item not found.")

        return item_repository.to_response(latest_record)

    @app.post("/items/{item_id}/summary", response_model=ItemResponse)
    def summary_item(
        item_id: str,
        background_tasks: BackgroundTasks,
        extended_output: bool = False,
    ) -> ItemResponse:
        record = item_repository.get_item(item_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Item not found.")

        transcript_for_summary = (record.enhanced_transcript_text or "").strip() or (record.transcript_text or "").strip()

        if record.source_type != "url":
            raise HTTPException(status_code=400, detail="Summary is only supported for URL items.")

        if transcript_for_summary == "":
            raise HTTPException(status_code=400, detail="Missing transcript_text. Run transcription first.")

        background_tasks.add_task(
            run_summary_job,
            item_id=item_id,
            item_repository=item_repository,
            anthropic_api_key=config.anthropic_api_key,
            extended_output=extended_output,
        )

        latest_record = item_repository.get_item(item_id)
        if latest_record is None:
            raise HTTPException(status_code=404, detail="Item not found.")

        return item_repository.to_response(latest_record)

    @app.get("/items/{item_id}", response_model=ItemResponse)
    def get_item(item_id: str) -> ItemResponse:
        record = item_repository.get_item(item_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Item not found.")

        return item_repository.to_response(record)

    @app.delete("/items/{item_id}")
    def delete_item(item_id: str) -> dict[str, bool]:
        record = item_repository.get_item(item_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Item not found.")

        # Best-effort delete of associated files.
        try:
            for filename in os.listdir(config.storage_dir):
                if filename.startswith(item_id):
                    try:
                        os.remove(os.path.join(config.storage_dir, filename))
                    except Exception:
                        pass

            if record.local_media_path:
                try:
                    if os.path.exists(record.local_media_path):
                        os.remove(record.local_media_path)
                except Exception:
                    pass
        except Exception:
            # Do not block DB deletion if storage cleanup fails.
            pass

        deleted = item_repository.delete_item(item_id)
        return {"deleted": deleted}

    return app


app = create_app()

