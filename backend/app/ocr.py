import base64
import json
import logging
import os
from io import BytesIO
from pathlib import Path
from time import perf_counter
from urllib.request import Request, urlopen

from PIL import Image, ImageChops, ImageOps, ImageStat, UnidentifiedImageError
import pytesseract

from .schemas import OcrResult

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
OCR_PRIMARY_CONFIG = "--oem 3 --psm 6 -c tessedit_do_invert=0"
OCR_FALLBACK_CONFIG = "--oem 3 --psm 11"
MIN_OCR_DIMENSION = 900
MAX_UPSCALE = 2
MAX_LONG_SIDE = 1400
WEAK_OCR_TEXT_LENGTH = 40
CLAUDE_VISION_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_VISION_MODEL = "claude-3-5-sonnet-latest"
CLAUDE_VISION_TIMEOUT_SECONDS = 20
logger = logging.getLogger(__name__)


def is_allowed_image_filename(filename: str) -> bool:
    return Path(filename or "").suffix.lower() in ALLOWED_EXTENSIONS


def _flatten_alpha(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        opaque_pixels = [pixel[:3] for pixel in rgba.getdata() if pixel[3] > 0]
        if opaque_pixels:
            sample = opaque_pixels[:: max(1, len(opaque_pixels) // 1000)]
            average = tuple(sum(channel) // len(sample) for channel in zip(*sample))
            background = (18, 22, 28) if sum(average) / 3 < 128 else (255, 255, 255)
        else:
            background = (255, 255, 255)
        canvas = Image.new("RGBA", rgba.size, background + (255,))
        canvas.paste(rgba, mask=alpha)
        return canvas.convert("RGB")
    return image.convert("RGB")


def _crop_uniform_margins(image: Image.Image) -> Image.Image:
    """Crop only obvious flat margins, avoiding aggressive content cropping."""
    rgb = image.convert("RGB")
    width, height = rgb.size
    if width < 80 or height < 80:
        return image

    edge_pixels = []
    edge_pixels.extend(rgb.crop((0, 0, width, 1)).getdata())
    edge_pixels.extend(rgb.crop((0, height - 1, width, height)).getdata())
    edge_pixels.extend(rgb.crop((0, 0, 1, height)).getdata())
    edge_pixels.extend(rgb.crop((width - 1, 0, width, height)).getdata())
    edge_sample = edge_pixels[:: max(1, len(edge_pixels) // 1000)]
    background = tuple(sum(channel) // len(edge_sample) for channel in zip(*edge_sample))

    background_image = Image.new("RGB", rgb.size, background)
    diff = ImageChops.difference(rgb, background_image).convert("L")
    mask = diff.point(lambda pixel: 255 if pixel > 18 else 0)
    bbox = mask.getbbox()
    if not bbox:
        return image

    left, top, right, bottom = bbox
    margin_x = max(3, int(width * 0.015))
    margin_y = max(3, int(height * 0.015))
    crop_box = (
        max(0, left - margin_x),
        max(0, top - margin_y),
        min(width, right + margin_x),
        min(height, bottom + margin_y),
    )
    crop_width = crop_box[2] - crop_box[0]
    crop_height = crop_box[3] - crop_box[1]
    crop_area_ratio = (crop_width * crop_height) / (width * height)
    removes_meaningful_margin = crop_width < width * 0.96 or crop_height < height * 0.96

    if removes_meaningful_margin and crop_area_ratio >= 0.55:
        return rgb.crop(crop_box)
    return image


def _resize_for_ocr(image: Image.Image) -> Image.Image:
    longest_side = max(image.size)
    if longest_side <= 0:
        return image
    if longest_side > MAX_LONG_SIDE:
        scale = MAX_LONG_SIDE / longest_side
        return image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    if longest_side >= MIN_OCR_DIMENSION:
        return image
    scale = min(MAX_UPSCALE, max(1, round(MIN_OCR_DIMENSION / longest_side)))
    if scale <= 1:
        return image
    return image.resize((image.width * scale, image.height * scale), Image.Resampling.LANCZOS)


def preprocess_image(image: Image.Image) -> Image.Image:
    image = _flatten_alpha(image)
    image = _crop_uniform_margins(image)
    image = _resize_for_ocr(image)
    image = image.convert("L")
    return ImageOps.autocontrast(image)


def _fallback_ocr_image(image: Image.Image) -> Image.Image:
    """Return a single bounded fallback image for very low primary OCR output."""
    grayscale = image.convert("L")
    mean_luminance = ImageStat.Stat(grayscale).mean[0]
    if mean_luminance < 128:
        return ImageOps.invert(grayscale)
    return grayscale


def _combine_ocr_outputs(outputs: list[str]) -> str:
    lines: list[str] = []
    seen: set[str] = set()
    for output in outputs:
        for raw_line in output.splitlines():
            line = " ".join(raw_line.split())
            if not line:
                continue
            key = line.casefold()
            if key not in seen:
                seen.add(key)
                lines.append(line)
    return "\n".join(lines)


def _image_media_type(filename: str) -> str:
    extension = Path(filename or "").suffix.lower()
    if extension == ".png":
        return "image/png"
    return "image/jpeg"


def _extract_text_with_claude_vision(image_bytes: bytes, filename: str) -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    payload = {
        "model": CLAUDE_VISION_MODEL,
        "max_tokens": 1200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": _image_media_type(filename),
                            "data": base64.b64encode(image_bytes).decode("ascii"),
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Transcribe all visible text from this alcohol beverage label. "
                            "Return plain OCR text only. Preserve line breaks when useful. "
                            "Do not summarize, explain, classify, or add text that is not visible."
                        ),
                    },
                ],
            }
        ],
    }
    request = Request(
        CLAUDE_VISION_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    started_at = perf_counter()
    try:
        with urlopen(request, timeout=CLAUDE_VISION_TIMEOUT_SECONDS) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        logger.info("Claude Vision OCR failed in %.3fs; falling back to Tesseract: %s", perf_counter() - started_at, exc)
        return None

    text_blocks = [
        block.get("text", "")
        for block in response_payload.get("content", [])
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    text = _combine_ocr_outputs(text_blocks).strip()
    logger.info("Claude Vision OCR completed in %.3fs", perf_counter() - started_at)
    if len(text) < 20:
        logger.info("Claude Vision OCR returned too little text; falling back to Tesseract")
        return None
    return text


def extract_text_from_image_bytes(image_bytes: bytes, filename: str = "label.png") -> OcrResult:
    total_started_at = perf_counter()
    if not image_bytes:
        return OcrResult(text="", status="REVIEW", message="No image bytes were provided.")
    if not is_allowed_image_filename(filename):
        return OcrResult(text="", status="FAIL", message="Only PNG or JPG label images are supported.")
    try:
        image = Image.open(BytesIO(image_bytes))
        claude_text = _extract_text_with_claude_vision(image_bytes, filename)
        if claude_text:
            logger.info("OCR extraction completed in %.3fs", perf_counter() - total_started_at)
            return OcrResult(text=claude_text, status="PASS", message="Claude Vision OCR completed successfully.")

        preprocess_started_at = perf_counter()
        processed = preprocess_image(image)
        logger.info("OCR preprocessing completed in %.3fs", perf_counter() - preprocess_started_at)

        ocr_started_at = perf_counter()
        primary_text = pytesseract.image_to_string(processed, config=OCR_PRIMARY_CONFIG)
        logger.info("OCR pass completed in %.3fs using primary config", perf_counter() - ocr_started_at)

        text = _combine_ocr_outputs([primary_text])
        if len(text.strip()) < WEAK_OCR_TEXT_LENGTH:
            fallback = _fallback_ocr_image(processed)
            fallback_started_at = perf_counter()
            fallback_text = pytesseract.image_to_string(fallback, config=OCR_FALLBACK_CONFIG)
            logger.info("OCR pass completed in %.3fs using fallback config", perf_counter() - fallback_started_at)
            text = _combine_ocr_outputs([primary_text, fallback_text])
    except UnidentifiedImageError:
        return OcrResult(text="", status="FAIL", message="Uploaded file could not be read as an image.")
    except pytesseract.TesseractNotFoundError:
        return OcrResult(text="", status="REVIEW", message="Tesseract OCR is not installed or not available in PATH.")
    except Exception as exc:
        return OcrResult(text="", status="REVIEW", message=f"OCR failed and needs manual review: {exc}")

    cleaned = text.strip()
    logger.info("OCR extraction completed in %.3fs", perf_counter() - total_started_at)
    if len(cleaned) < 20:
        return OcrResult(text=cleaned, status="REVIEW", message="OCR extracted very little text; manual review recommended.")
    return OcrResult(text=cleaned, status="PASS", message="OCR completed successfully.")
