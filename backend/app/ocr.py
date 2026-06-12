from io import BytesIO
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps, UnidentifiedImageError
import pytesseract

from .schemas import OcrResult

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def is_allowed_image_filename(filename: str) -> bool:
    return Path(filename or "").suffix.lower() in ALLOWED_EXTENSIONS


def preprocess_image(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    image = image.convert("L")
    image = ImageEnhance.Contrast(image).enhance(1.7)
    return image


def extract_text_from_image_bytes(image_bytes: bytes, filename: str = "label.png") -> OcrResult:
    if not image_bytes:
        return OcrResult(text="", status="REVIEW", message="No image bytes were provided.")
    if not is_allowed_image_filename(filename):
        return OcrResult(text="", status="FAIL", message="Only PNG or JPG label images are supported.")
    try:
        image = Image.open(BytesIO(image_bytes))
        processed = preprocess_image(image)
        text = pytesseract.image_to_string(processed, config="--psm 6")
    except UnidentifiedImageError:
        return OcrResult(text="", status="FAIL", message="Uploaded file could not be read as an image.")
    except pytesseract.TesseractNotFoundError:
        return OcrResult(text="", status="REVIEW", message="Tesseract OCR is not installed or not available in PATH.")
    except Exception as exc:
        return OcrResult(text="", status="REVIEW", message=f"OCR failed and needs manual review: {exc}")

    cleaned = text.strip()
    if len(cleaned) < 20:
        return OcrResult(text=cleaned, status="REVIEW", message="OCR extracted very little text; manual review recommended.")
    return OcrResult(text=cleaned, status="PASS", message="OCR completed successfully.")
