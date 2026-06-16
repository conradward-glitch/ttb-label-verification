import logging
from io import BytesIO
from pathlib import Path
from time import perf_counter

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


def extract_text_from_image_bytes(image_bytes: bytes, filename: str = "label.png") -> OcrResult:
    total_started_at = perf_counter()
    if not image_bytes:
        return OcrResult(text="", status="REVIEW", message="No image bytes were provided.")
    if not is_allowed_image_filename(filename):
        return OcrResult(text="", status="FAIL", message="Only PNG or JPG label images are supported.")
    try:
        image = Image.open(BytesIO(image_bytes))

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
