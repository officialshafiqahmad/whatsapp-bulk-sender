from __future__ import annotations

import json
import os
import queue
import threading
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from excel_import import ExcelImportError, parse_excel_phone_list
from whatsapp_core import (
    Contact,
    get_session_dir,
    load_config,
    parse_phone_list,
    send_bulk_messages,
    verify_browser_launch,
    verify_whatsapp_connectivity,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
CONFIG_PATH = BASE_DIR / "config.json"
if os.environ.get("SPACE_ID") or os.environ.get("HEADLESS") == "true":
    CONFIG_PATH = BASE_DIR / "config.production.json"

app = FastAPI(title="WhatsApp Bulk Sender")

allowed_origins = [
    "http://127.0.0.1:8765",
    "http://localhost:8765",
    "https://officialshafiqahmad.github.io",
]
public_app_url = os.environ.get("PUBLIC_APP_URL")
if public_app_url:
    allowed_origins.append(public_app_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.(trycloudflare|hf)\.(com|space)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_send_lock = threading.Lock()
_send_thread: threading.Thread | None = None


def _clear_stale_send_lock() -> None:
    global _send_thread
    if _send_thread is not None and not _send_thread.is_alive():
        _send_thread = None
        if _send_lock.locked():
            try:
                _send_lock.release()
            except RuntimeError:
                pass


class SendRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    phones: list[str] = Field(min_length=1)
    delay_seconds: int = Field(default=5, ge=2, le=60)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/browser-check")
def browser_check() -> dict:
    try:
        return verify_browser_launch()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/whatsapp-check")
def whatsapp_check() -> dict:
    try:
        return verify_whatsapp_connectivity()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/import-excel")
async def import_excel(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    try:
        phones = parse_excel_phone_list(content, file.filename)
    except ExcelImportError as exc:
        raise HTTPException(
            status_code=400,
            detail={"message": exc.message, "details": exc.details},
        ) from exc

    return {
        "phones": phones,
        "count": len(phones),
        "message": f"Imported {len(phones)} phone numbers successfully.",
    }


@app.post("/api/validate-phones")
def validate_phones(payload: SendRequest) -> dict:
    try:
        contacts = [Contact(name=p, phone=p) for p in payload.phones]
        if not contacts:
            raise ValueError("No phone numbers provided.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "count": len(contacts),
        "phones": [c.phone for c in contacts],
        "message": f"{len(contacts)} phone numbers ready to send.",
    }


@app.post("/api/send")
def start_send(payload: SendRequest) -> StreamingResponse:
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        contacts = parse_phone_list("\n".join(payload.phones))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not contacts:
        raise HTTPException(status_code=400, detail="Add at least one phone number.")

    _clear_stale_send_lock()
    if not _send_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="A send job is already running. Please wait for it to finish.")

    config = load_config(CONFIG_PATH if CONFIG_PATH.exists() else None)
    delay_seconds = payload.delay_seconds or config.get("delay_seconds", 5)
    headless = config.get("headless", bool(os.environ.get("SPACE_ID")))
    if os.environ.get("SPACE_ID"):
        session_dir = get_session_dir()
    else:
        session_dir = BASE_DIR / config.get("session_dir", ".whatsapp-session")

    event_queue: queue.Queue[dict | None] = queue.Queue()

    def on_progress(event: dict) -> None:
        event_queue.put(event)

    def run_job() -> None:
        try:
            send_bulk_messages(
                contacts,
                message,
                delay_seconds=delay_seconds,
                headless=headless,
                session_dir=session_dir,
                on_progress=on_progress,
            )
        except Exception as exc:
            event_queue.put({"type": "error", "message": str(exc)})
        finally:
            event_queue.put(None)
            _send_lock.release()

    thread = threading.Thread(target=run_job, daemon=True)
    global _send_thread
    _send_thread = thread
    thread.start()

    def event_stream():
        while True:
            event = event_queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8765"))
    uvicorn.run("app:app", host=host, port=port, reload=False)
