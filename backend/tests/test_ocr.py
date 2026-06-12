from app.ocr import is_allowed_image_filename, extract_text_from_image_bytes


def test_allowed_image_extensions():
    assert is_allowed_image_filename("label.png")
    assert is_allowed_image_filename("label.jpg")
    assert is_allowed_image_filename("label.jpeg")
    assert not is_allowed_image_filename("label.pdf")


def test_empty_image_bytes_returns_review_signal():
    result = extract_text_from_image_bytes(b"", "empty.png")
    assert result.status == "REVIEW"
    assert result.text == ""
