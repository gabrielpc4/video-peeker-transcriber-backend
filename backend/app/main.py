import os
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import AppConfig, load_config
from .db import Database, initialize_database
from .metadata import try_resolve_title
from .models import CreateItemResponse, CreateUrlItemRequest, ItemResponse
from .repository import ItemRepository
from .tasks import run_breakdown_job, run_transcription_job


def create_app() -> FastAPI:
    app = FastAPI(title="VibeRecap Backend")

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

    @app.post("/items", response_model=CreateItemResponse)
    def create_url_item(request: CreateUrlItemRequest) -> CreateItemResponse:
        source_url = request.source_url.strip()
        if source_url == "":
            raise HTTPException(status_code=400, detail="source_url is empty.")

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

        temporary_path = os.path.join(config.storage_dir, f"upload-temp{safe_extension}")
        with open(temporary_path, "wb") as output_handle:
            output_handle.write(content)

        item_id = item_repository.create_upload_item(local_media_path=temporary_path)
        return CreateItemResponse(item_id=item_id)

    @app.post("/items/{item_id}/transcribe", response_model=ItemResponse)
    def transcribe_item(item_id: str, background_tasks: BackgroundTasks) -> ItemResponse:
        record = item_repository.get_item(item_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Item not found.")

        background_tasks.add_task(
            run_transcription_job,
            item_id=item_id,
            item_repository=item_repository,
            storage_dir=config.storage_dir,
            instagram_cookies_path=config.instagram_cookies_path,
            assemblyai_api_key=config.assemblyai_api_key,
        )

        latest_record = item_repository.get_item(item_id)
        if latest_record is None:
            raise HTTPException(status_code=404, detail="Item not found.")

        return item_repository.to_response(latest_record)

    @app.post("/items/{item_id}/breakdown", response_model=ItemResponse)
    def breakdown_item(item_id: str, background_tasks: BackgroundTasks) -> ItemResponse:
        record = item_repository.get_item(item_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Item not found.")

        if (record.transcript_text or "").strip() == "":
            raise HTTPException(status_code=400, detail="Missing transcript_text. Run transcription first.")

        background_tasks.add_task(
            run_breakdown_job,
            item_id=item_id,
            item_repository=item_repository,
            anthropic_api_key=config.anthropic_api_key,
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

    return app


app = create_app()

