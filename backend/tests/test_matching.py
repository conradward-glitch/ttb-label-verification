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


def test_passing_bourbon_label_returns_pass():
    result = verify_application(valid_label_text(), valid_application())

    assert result["overall_status"] == "PASS"
    assert all(field["status"] == "PASS" for field in result["fields"])


def test_abv_mismatch_returns_fail_with_field_explanation():
    application = valid_application()
    application["alcohol_content"] = "40% Alc./Vol. (80 Proof)"

    result = verify_application(valid_label_text(), application)

    assert result["overall_status"] == "FAIL"
    abv = next(field for field in result["fields"] if field["field"] == "Alcohol Content")
    assert abv["status"] == "FAIL"
    assert "expected" in abv["message"].lower()
    assert "found" in abv["message"].lower()


def test_missing_government_warning_returns_fail():
    text = "OLD TOM DISTILLERY Kentucky Straight Bourbon Whiskey 45% Alc./Vol. (90 Proof) 750 mL"

    result = verify_application(text, valid_application())

    assert result["overall_status"] == "FAIL"
    warning = next(field for field in result["fields"] if field["field"] == "Government Warning")
    assert warning["status"] == "FAIL"
    assert "warning" in warning["message"].lower()


def test_brand_name_tolerates_case_and_apostrophe_style():
    application = valid_application()
    application["brand_name"] = "Stone's Throw"
    text = valid_label_text().replace("OLD TOM DISTILLERY", "STONE’S THROW")

    result = verify_application(text, application)

    brand = next(field for field in result["fields"] if field["field"] == "Brand Name")
    assert brand["status"] == "PASS"
