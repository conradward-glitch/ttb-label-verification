import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from .matching import verify_application
from .ocr import extract_text_from_image_bytes, is_allowed_image_filename
from .schemas import ApplicationData

app = FastAPI(title="TTB Label Verification Prototype", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, Any]:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    return {"status": "ok", "key_loaded": bool(key), "key_prefix": key[:8] if key else "none"}


@app.post("/api/ocr")
async def ocr_only(label_image: UploadFile = File(...)) -> dict[str, Any]:
    if not is_allowed_image_filename(label_image.filename or ""):
        raise HTTPException(status_code=400, detail="Only PNG or JPG label images are supported.")
    image_bytes = await label_image.read()
    result = extract_text_from_image_bytes(image_bytes, label_image.filename or "label.png")
    return result.model_dump()


@app.post("/api/verify")
async def verify_label(
    application_data: str = Form(...),
    label_image: UploadFile = File(...),
) -> dict[str, Any]:
    if not is_allowed_image_filename(label_image.filename or ""):
        raise HTTPException(status_code=400, detail="Only PNG or JPG label images are supported.")
    try:
        parsed_application = json.loads(application_data)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="application_data must be valid JSON.") from exc
    if not isinstance(parsed_application, dict):
        raise HTTPException(status_code=400, detail="application_data must be a JSON object.")
    try:
        parsed_application = ApplicationData.model_validate(parsed_application).model_dump()
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail="application_data does not match the expected schema.") from exc

    image_bytes = await label_image.read()
    ocr_result = extract_text_from_image_bytes(image_bytes, label_image.filename or "label.png")
    verification = verify_application(ocr_result.text, parsed_application)
    verification["ocr_status"] = ocr_result.status
    verification["ocr_message"] = ocr_result.message
    if ocr_result.status == "REVIEW" and verification["overall_status"] == "PASS":
        verification["overall_status"] = "REVIEW"
        verification["summary"] = "OCR quality requires manual review before approval."
    return verification


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        requested = frontend_dist / full_path
        if full_path and requested.exists() and requested.is_file():
            return FileResponse(requested)
        return FileResponse(frontend_dist / "index.html")
