from app.warning import validate_government_warning


VALID_WARNING = "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."


def test_valid_warning_passes():
    result = validate_government_warning(VALID_WARNING)
    assert result.status == "PASS"


def test_title_case_warning_prefix_fails():
    result = validate_government_warning(VALID_WARNING.replace("GOVERNMENT WARNING:", "Government Warning:"))
    assert result.status == "FAIL"
    assert "all caps" in result.message.lower()


def test_materially_altered_warning_fails():
    altered = VALID_WARNING.replace("birth defects", "bad outcomes")
    result = validate_government_warning(altered)
    assert result.status == "FAIL"


def test_warning_like_ocr_without_exact_prefix_returns_review_not_fail():
    ocr_text = """
    GOVERNMENT WARNINC (1) According to the Surgeon Genera1 women should not drink
    alcoholic beverages during pregnancy because of the risk of birth defects.
    (2) Consumption of alcoholic beverages impairs your ability to drive a car or
    operate machinery, and may cause health problems.
    """

    result = validate_government_warning(ocr_text)

    assert result.status == "REVIEW"
    assert "warning-like" in result.message.lower()


def test_partial_warning_ocr_returns_review_not_fail():
    ocr_text = """
    GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink
    alcoholic beverages during pregnancy because of the risk of birth defects.
    """

    result = validate_government_warning(ocr_text)

    assert result.status == "REVIEW"
    assert "partial" in result.message.lower() or "manual review" in result.message.lower()


def test_garbled_warning_with_required_anchors_returns_review_not_fail():
    ocr_text = """
    GOVERNMENT WARNING: (1) According 10 the Surgeon General women should not drink
    alcoholic beverages during pregnancy because of the risk of birth defects.
    (2) Consumption of alcoholic beverages impairs your ability to drive a car or
    operate machinery, and may cause health problems.
    """

    result = validate_government_warning(ocr_text)

    assert result.status == "REVIEW"
    assert "ocr" in result.message.lower() or "manual review" in result.message.lower()
