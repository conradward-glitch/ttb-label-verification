from app.matching import verify_application


def valid_application():
    return {
        "brand_name": "OLD TOM DISTILLERY",
        "class_type": "Kentucky Straight Bourbon Whiskey",
        "alcohol_content": "45% Alc./Vol. (90 Proof)",
        "net_contents": "750 mL",
        "bottler_producer": "Bottled by Old Tom Distillery, Louisville, KY",
        "country_of_origin": "",
    }


def valid_label_text():
    return """
    OLD TOM DISTILLERY
    Kentucky Straight Bourbon Whiskey
    45% Alc./Vol. (90 Proof)
    750 mL
    Bottled by Old Tom Distillery, Louisville, KY
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


def test_proof_only_alcohol_match_displays_raw_proof_and_normalized_abv():
    text = valid_label_text().replace("45% Alc./Vol. (90 Proof)", "90 PROOF")

    result = verify_application(text, valid_application())

    abv = field(result, "Alcohol Content")
    assert abv["status"] == "PASS"
    assert abv["found"] == "90 PROOF"
    assert abv["evidence"] == "Normalized: 45% ABV"
    assert abv["message"] == "Alcohol content matches the application because 90 proof is equivalent to 45% ABV."


def test_literal_abv_match_displays_literal_abv_as_found():
    text = valid_label_text().replace("45% Alc./Vol. (90 Proof)", "45% ABV")

    result = verify_application(text, valid_application())

    abv = field(result, "Alcohol Content")
    assert abv["status"] == "PASS"
    assert abv["found"] == "45% ABV"
    assert abv["evidence"] == "45% ABV"
    assert abv["message"] == "Alcohol content matches the application."


def test_missing_government_warning_returns_fail():
    text = "OLD TOM DISTILLERY Kentucky Straight Bourbon Whiskey 45% Alc./Vol. (90 Proof) 750 mL Bottled by Old Tom Distillery, Louisville, KY"

    result = verify_application(text, valid_application())

    assert result["overall_status"] == "FAIL"
    warning = field(result, "Government Warning")
    assert warning["status"] == "FAIL"
    assert "warning" in warning["message"].lower()


def test_bottler_producer_missing_from_application_returns_review():
    application = valid_application()
    application["bottler_producer"] = ""

    result = verify_application(valid_label_text(), application)

    bottler = field(result, "Bottler/Producer Name and Address")
    assert result["overall_status"] == "REVIEW"
    assert bottler["status"] == "REVIEW"
    assert "not supplied" in bottler["message"].lower()


def test_bottler_producer_present_and_found_returns_pass():
    result = verify_application(valid_label_text(), valid_application())

    bottler = field(result, "Bottler/Producer Name and Address")
    assert bottler["status"] == "PASS"
    assert "Old Tom Distillery" in bottler["evidence"]


def test_bottler_producer_present_and_absent_returns_fail_or_review():
    application = valid_application()
    application["bottler_producer"] = "Bottled by Different Distillery, Nashville, TN"

    result = verify_application(valid_label_text(), application)

    bottler = field(result, "Bottler/Producer Name and Address")
    assert bottler["status"] in {"FAIL", "REVIEW"}
    assert bottler["status"] != "PASS"


def test_country_of_origin_blank_is_ignored():
    result = verify_application(valid_label_text(), valid_application())

    assert all(field["field"] != "Country of Origin" for field in result["fields"])
    assert result["overall_status"] == "PASS"


def test_country_of_origin_supplied_and_present_returns_pass():
    application = valid_application()
    application["country_of_origin"] = "Mexico"
    text = valid_label_text() + "\nProduct of Mexico"

    result = verify_application(text, application)

    country = field(result, "Country of Origin")
    assert country["status"] == "PASS"


def test_country_of_origin_usa_passes_from_state_address_evidence():
    application = valid_application()
    application["country_of_origin"] = "USA"

    result = verify_application(valid_label_text(), application)

    country = field(result, "Country of Origin")
    assert country["status"] == "PASS"
    assert country["evidence"]


def test_country_of_origin_supplied_and_absent_returns_fail_or_review():
    application = valid_application()
    application["country_of_origin"] = "France"

    result = verify_application(valid_label_text(), application)

    country = field(result, "Country of Origin")
    assert country["status"] in {"FAIL", "REVIEW"}
    assert country["status"] != "PASS"


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


def test_class_type_passes_when_expected_tokens_are_adjacent_across_lines():
    text = valid_label_text().replace("Kentucky Straight Bourbon Whiskey", "KENTUCKY STRAIGHT\n    BOURBON WHISKEY")

    result = verify_application(text, valid_application())

    class_type = field(result, "Class/Type")
    assert class_type["status"] == "PASS"
    assert class_type["found"] == "KENTUCKY STRAIGHT\nBOURBON WHISKEY"
    assert class_type["evidence"] == "KENTUCKY STRAIGHT\nBOURBON WHISKEY"


def test_weak_brand_ocr_evidence_returns_review_not_fail():
    text = valid_label_text().replace("OLD TOM DISTILLERY", "Old Torn Distil1ery")
    text = text.replace("Bottled by Old Tom Distillery, Louisville, KY", "Bottled by OTD, Louisville, KY")

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


def test_old_tom_noisy_combined_ocr_returns_sensible_review_not_fail():
    text = """
    oLD TON
    eA SS
    | KENTUCKY STRAIGHT |,
    | BOURBONWHISKEY |
    | HAND-CRAFTED TRADITION |
    | GOVERNMENT WARNING: (1) According to the |
    Surgeon General, women should not drink =f /
    alcoholic beverages during pregnancy because of |
    the risk of birth defects. (2) Consumption of //
    alcoholic beverages impairs your ability to”
    drive a car or operate machinery, {7 .”
    and may cause health |
    problems. A
    OLD TO
    pist
    ILLERy
    te
    ° was
    2/ =
    KENTUCKY. STRA GHT
    +0
    f,
    BOURBON WHISKEY
    is ae
    750 mL
    90 PROOF :
    Bottled by OTD, Louisville, KY
    HAND: CRAFTED TRADITION
    GOVERNMENT WARNING: (1) According to the
    Surgeon General, women should not drink
    alcoholic beverages during pregnancy because of
    the risk of birth defects. (2) Consumption of
    alcoholic beverages impairs your ability to bl
    drive a car or operate machinery,
    and may cause health
    problems
    HAND- —_ TRADITION
    problems. 4
    """

    result = verify_application(text, valid_application())

    assert result["overall_status"] == "REVIEW"
    assert field(result, "Brand Name")["status"] == "REVIEW"
    assert field(result, "Class/Type")["status"] == "PASS"
    assert field(result, "Alcohol Content")["status"] == "PASS"
    assert field(result, "Net Contents")["status"] == "PASS"
    assert field(result, "Government Warning")["status"] == "REVIEW"
