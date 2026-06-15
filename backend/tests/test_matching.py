from app.matching import verify_application


def valid_application():
    return {
        "brand_name": "OLD TOM DISTILLERY",
        "class_type": "Kentucky Straight Bourbon Whiskey",
        "alcohol_content": "45% Alc./Vol. (90 Proof)",
        "net_contents": "750 mL",
    }


def valid_label_text():
    return """
    OLD TOM DISTILLERY
    Kentucky Straight Bourbon Whiskey
    45% Alc./Vol. (90 Proof)
    750 mL
    GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.
    """


def field(result, name):
    return next(field for field in result["fields"] if field["field"] == name)


def test_passing_bourbon_label_returns_pass():
    result = verify_application(valid_label_text(), valid_application())

    assert result["overall_status"] == "PASS"
    assert all(field["status"] == "PASS" for field in result["fields"])


def test_abv_mismatch_returns_fail_with_field_explanation():
    application = valid_application()
    application["alcohol_content"] = "40% Alc./Vol. (80 Proof)"

    result = verify_application(valid_label_text(), application)

    assert result["overall_status"] == "FAIL"
    abv = field(result, "Alcohol Content")
    assert abv["status"] == "FAIL"
    assert "expected" in abv["message"].lower()
    assert "found" in abv["message"].lower()


def test_missing_government_warning_returns_fail():
    text = "OLD TOM DISTILLERY Kentucky Straight Bourbon Whiskey 45% Alc./Vol. (90 Proof) 750 mL"

    result = verify_application(text, valid_application())

    assert result["overall_status"] == "FAIL"
    warning = field(result, "Government Warning")
    assert warning["status"] == "FAIL"
    assert "warning" in warning["message"].lower()


def test_brand_name_tolerates_case_and_apostrophe_style():
    application = valid_application()
    application["brand_name"] = "Stone's Throw"
    text = valid_label_text().replace("OLD TOM DISTILLERY", "STONE’S THROW")

    result = verify_application(text, application)

    brand = field(result, "Brand Name")
    assert brand["status"] == "PASS"


def test_brand_name_tolerates_case_punctuation_apostrophes_hyphens_and_whitespace():
    application = valid_application()
    application["brand_name"] = "Maker's-Mark   Reserve"
    text = valid_label_text().replace("OLD TOM DISTILLERY", "MAKERS MARK RESERVE")

    result = verify_application(text, application)

    brand = field(result, "Brand Name")
    assert brand["status"] == "PASS"


def test_class_type_tolerates_punctuation_hyphens_and_slashes():
    application = valid_application()
    application["class_type"] = "Kentucky Straight-Bourbon/Whiskey"
    text = valid_label_text().replace("Kentucky Straight Bourbon Whiskey", "kentucky straight bourbon whiskey")

    result = verify_application(text, application)

    class_type = field(result, "Class/Type")
    assert class_type["status"] == "PASS"


def test_weak_brand_ocr_evidence_returns_review_not_fail():
    text = valid_label_text().replace("OLD TOM DISTILLERY", "Old Torn Distil1ery")

    result = verify_application(text, valid_application())

    brand = field(result, "Brand Name")
    assert result["overall_status"] == "REVIEW"
    assert brand["status"] == "REVIEW"
    assert brand["evidence"] == "Old Torn Distil1ery"


def test_net_contents_tolerates_case_punctuation_hyphens_and_whitespace():
    text = valid_label_text().replace("750 mL", "750-m.l.")

    result = verify_application(text, valid_application())

    net_contents = field(result, "Net Contents")
    assert net_contents["status"] == "PASS"


def test_weak_net_contents_ocr_evidence_returns_review_not_fail():
    text = valid_label_text().replace("750 mL", "750 rnL")

    result = verify_application(text, valid_application())

    net_contents = field(result, "Net Contents")
    assert result["overall_status"] == "REVIEW"
    assert net_contents["status"] == "REVIEW"
    assert net_contents["evidence"] == "750 rnL"


def test_warning_like_ocr_makes_overall_review_not_fail():
    text = valid_label_text().replace("GOVERNMENT WARNING:", "GOVERNMENT WARNINC")
    text = text.replace("Surgeon General", "Surgeon Genera1")

    result = verify_application(text, valid_application())

    assert result["overall_status"] == "REVIEW"
    warning = field(result, "Government Warning")
    assert warning["status"] == "REVIEW"
    assert "manual review" in warning["message"].lower() or "warning-like" in warning["message"].lower()
