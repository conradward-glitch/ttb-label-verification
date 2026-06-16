from io import BytesIO

from PIL import Image, ImageStat

from app import ocr
from app.ocr import extract_text_from_image_bytes, is_allowed_image_filename, preprocess_image


def png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_allowed_image_extensions():
    assert is_allowed_image_filename("label.png")
    assert is_allowed_image_filename("label.jpg")
    assert is_allowed_image_filename("label.jpeg")
    assert not is_allowed_image_filename("label.pdf")


def test_empty_image_bytes_returns_review_signal():
    result = extract_text_from_image_bytes(b"", "empty.png")
    assert result.status == "REVIEW"
    assert result.text == ""


def test_preprocess_handles_alpha_and_upscales_low_resolution_labels():
    image = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    image.paste((12, 24, 36, 255), (20, 20, 80, 60))

    processed = preprocess_image(image)

    assert processed.mode == "L"
    assert processed.size[0] >= 300
    assert processed.size[1] >= 240


def test_extract_text_uses_one_primary_tesseract_pass_when_text_is_sufficient(monkeypatch):
    calls = []

    def fake_image_to_string(image, config):
        calls.append((image.size, config))
        return "OLD TOM DISTILLERY\nKENTUCKY STRAIGHT BOURBON WHISKEY\n45% Alc./Vol. (90 Proof)\n750 mL\n"

    monkeypatch.setattr(ocr.pytesseract, "image_to_string", fake_image_to_string)
    image = Image.new("RGBA", (120, 90), (15, 20, 30, 255))

    result = extract_text_from_image_bytes(png_bytes(image), "label.png")

    assert len(calls) == 1
    assert calls[0][1] == ocr.PRIMARY_OCR_CONFIG
    assert calls[0][0][0] >= 360 and calls[0][0][1] >= 270
    assert result.status == "PASS"
    assert "OLD TOM DISTILLERY" in result.text
    assert "KENTUCKY STRAIGHT BOURBON WHISKEY" in result.text
    assert "750 mL" in result.text


def test_extract_text_runs_one_fallback_only_when_primary_returns_almost_no_text(monkeypatch):
    calls = []

    def fake_image_to_string(image, config):
        mean_luminance = ImageStat.Stat(image.convert("L")).mean[0]
        calls.append((mean_luminance, config))
        if len(calls) == 1:
            return "OLD"
        return "OLD TOM DISTILLERY\nKENTUCKY STRAIGHT BOURBON WHISKEY\n45% Alc./Vol. (90 Proof)\n750 mL\n"

    monkeypatch.setattr(ocr.pytesseract, "image_to_string", fake_image_to_string)
    image = Image.new("RGBA", (140, 100), (8, 12, 18, 255))
    image.paste((245, 238, 210, 255), (35, 30, 105, 70))

    result = extract_text_from_image_bytes(png_bytes(image), "old-tom.png")

    assert len(calls) == 2
    assert calls[1][1] == ocr.FALLBACK_OCR_CONFIG
    assert result.status == "PASS"
    assert "OLD TOM DISTILLERY" in result.text
    assert "KENTUCKY STRAIGHT BOURBON WHISKEY" in result.text
