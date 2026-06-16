import json
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


def test_ocr_uses_bounded_configs_and_image_sizing():
    assert ocr.OCR_PRIMARY_CONFIG == "--oem 3 --psm 6 -c tessedit_do_invert=0"
    assert ocr.OCR_FALLBACK_CONFIG == "--oem 3 --psm 11"
    assert ocr.MIN_OCR_DIMENSION == 900
    assert ocr.MAX_UPSCALE == 2
    assert ocr.MAX_LONG_SIDE == 1400


def test_claude_vision_uses_current_sonnet_model():
    assert ocr.CLAUDE_VISION_MODEL == "claude-sonnet-4-6"


def test_preprocess_handles_alpha_and_upscales_low_resolution_labels():
    image = Image.new("RGBA", (100, 80), (0, 0, 0, 0))
    image.paste((12, 24, 36, 255), (20, 20, 80, 60))

    processed = preprocess_image(image)

    assert processed.size[0] >= 200
    assert processed.size[1] >= 160


def test_preprocess_downscales_large_images_before_ocr():
    image = Image.new("RGB", (2800, 2100), (255, 255, 255))

    processed = preprocess_image(image)

    assert max(processed.size) == ocr.MAX_LONG_SIDE


def test_extract_text_uses_one_primary_tesseract_pass_when_text_is_sufficient(monkeypatch):
    calls = []

    def fake_image_to_string(image, config):
        calls.append((image.size, config))
        return "OLD TOM DISTILLERY\nKENTUCKY STRAIGHT BOURBON WHISKEY\n45% Alc./Vol. (90 Proof)\n750 mL\n"

    monkeypatch.setattr(ocr.pytesseract, "image_to_string", fake_image_to_string)
    image = Image.new("RGBA", (120, 90), (15, 20, 30, 255))

    result = extract_text_from_image_bytes(png_bytes(image), "label.png")

    assert len(calls) == 1
    assert calls[0][1] == ocr.OCR_PRIMARY_CONFIG
    assert calls[0][0][0] >= 240 and calls[0][0][1] >= 180
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
    assert calls[1][1] == ocr.OCR_FALLBACK_CONFIG
    assert result.status == "PASS"
    assert "OLD TOM DISTILLERY" in result.text
    assert "KENTUCKY STRAIGHT BOURBON WHISKEY" in result.text


def test_primary_ocr_under_40_cleaned_characters_triggers_one_fallback(monkeypatch):
    calls = []

    def fake_image_to_string(image, config):
        calls.append(config)
        if len(calls) == 1:
            return "1234567890\n1234567890\n12345678901234567"
        return "OLD TOM DISTILLERY\nKENTUCKY STRAIGHT BOURBON WHISKEY\n45% Alc./Vol. (90 Proof)\n750 mL\n"

    monkeypatch.setattr(ocr.pytesseract, "image_to_string", fake_image_to_string)
    image = Image.new("RGB", (160, 120), (240, 240, 240))

    result = extract_text_from_image_bytes(png_bytes(image), "label.png")

    assert calls == [ocr.OCR_PRIMARY_CONFIG, ocr.OCR_FALLBACK_CONFIG]
    assert result.status == "PASS"
    assert "OLD TOM DISTILLERY" in result.text


def test_extract_text_logs_preprocessing_ocr_and_total_timing(monkeypatch, caplog):
    def fake_image_to_string(image, config):
        return "OLD TOM DISTILLERY\nKENTUCKY STRAIGHT BOURBON WHISKEY\n45% Alc./Vol. (90 Proof)\n750 mL\n"

    monkeypatch.setattr(ocr.pytesseract, "image_to_string", fake_image_to_string)
    image = Image.new("RGB", (160, 120), (240, 240, 240))

    with caplog.at_level("INFO", logger="app.ocr"):
        result = extract_text_from_image_bytes(png_bytes(image), "label.png")

    messages = "\n".join(record.getMessage() for record in caplog.records)
    assert result.status == "PASS"
    assert "OCR preprocessing completed" in messages
    assert "OCR pass completed" in messages
    assert "OCR extraction completed" in messages


class FakeClaudeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_claude_vision_success_is_used_before_tesseract(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    requests = []

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        return FakeClaudeResponse(
            {
                "content": [
                    {
                        "type": "text",
                        "text": "OLD TOM DISTILLERY\nKentucky Straight Bourbon Whiskey\n45% Alc./Vol. (90 Proof)\n750 mL",
                    }
                ]
            }
        )

    def fail_if_tesseract_runs(image, config):
        raise AssertionError("Tesseract should not run when Claude Vision returns usable OCR text")

    monkeypatch.setattr(ocr, "urlopen", fake_urlopen, raising=False)
    monkeypatch.setattr(ocr.pytesseract, "image_to_string", fail_if_tesseract_runs)

    result = extract_text_from_image_bytes(png_bytes(Image.new("RGB", (160, 120), (240, 240, 240))), "label.png")

    assert result.status == "PASS"
    assert result.message == "Claude Vision OCR completed successfully."
    assert "OLD TOM DISTILLERY" in result.text
    assert len(requests) == 1
    assert requests[0][1] == ocr.CLAUDE_VISION_TIMEOUT_SECONDS


def test_missing_anthropic_key_preserves_tesseract_behavior(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    calls = []

    def fail_if_claude_runs(request, timeout):
        raise AssertionError("Claude Vision should not run without ANTHROPIC_API_KEY")

    def fake_image_to_string(image, config):
        calls.append(config)
        return "OLD TOM DISTILLERY\nKENTUCKY STRAIGHT BOURBON WHISKEY\n45% Alc./Vol. (90 Proof)\n750 mL\n"

    monkeypatch.setattr(ocr, "urlopen", fail_if_claude_runs, raising=False)
    monkeypatch.setattr(ocr.pytesseract, "image_to_string", fake_image_to_string)

    result = extract_text_from_image_bytes(png_bytes(Image.new("RGB", (160, 120), (240, 240, 240))), "label.png")

    assert calls == [ocr.OCR_PRIMARY_CONFIG]
    assert result.status == "PASS"
    assert result.message == "OCR completed successfully."
    assert "OLD TOM DISTILLERY" in result.text


def test_claude_vision_failure_falls_back_to_tesseract(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    tesseract_calls = []

    def fail_claude(request, timeout):
        raise RuntimeError("claude unavailable")

    def fake_image_to_string(image, config):
        tesseract_calls.append(config)
        return "OLD TOM DISTILLERY\nKENTUCKY STRAIGHT BOURBON WHISKEY\n45% Alc./Vol. (90 Proof)\n750 mL\n"

    monkeypatch.setattr(ocr, "urlopen", fail_claude, raising=False)
    monkeypatch.setattr(ocr.pytesseract, "image_to_string", fake_image_to_string)

    result = extract_text_from_image_bytes(png_bytes(Image.new("RGB", (160, 120), (240, 240, 240))), "label.png")

    assert tesseract_calls == [ocr.OCR_PRIMARY_CONFIG]
    assert result.status == "PASS"
    assert result.message == "OCR completed successfully."
    assert "OLD TOM DISTILLERY" in result.text
