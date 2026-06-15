from io import BytesIO

from PIL import Image

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


def test_extract_text_runs_multiple_tesseract_psm_passes_and_combines_unique_output(monkeypatch):
    calls = []

    def fake_image_to_string(image, config):
        calls.append((image.size, config))
        if "--psm 6" in config:
            return "OLD TOM\nDISTILLERY\n"
        if "--psm 11" in config:
            return "KENTUCKY STRAIGHT BOURBON WHISKEY\n750 mL\n"
        if "--psm 4" in config:
            return "90 PROOF\nOLD TOM\n"
        return ""

    monkeypatch.setattr(ocr.pytesseract, "image_to_string", fake_image_to_string)
    image = Image.new("RGBA", (120, 90), (15, 20, 30, 255))

    result = extract_text_from_image_bytes(png_bytes(image), "label.png")

    configs = [config for _, config in calls]
    assert any("--psm 6" in config for config in configs)
    assert any("--psm 11" in config for config in configs)
    assert any("--psm 4" in config for config in configs)
    assert all(size[0] >= 360 and size[1] >= 270 for size, _ in calls)
    assert result.status == "PASS"
    assert result.text.count("OLD TOM") == 1
    assert "DISTILLERY" in result.text
    assert "KENTUCKY STRAIGHT BOURBON WHISKEY" in result.text
    assert "750 mL" in result.text
    assert "90 PROOF" in result.text
