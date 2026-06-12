import json
from pathlib import Path

from PIL import Image

from app.matching import verify_application

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "samples"

PASSING_LABEL_TEXT = """
OLD TOM DISTILLERY
Kentucky Straight Bourbon Whiskey
45% Alc./Vol. (90 Proof)
750 mL
GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.
"""

WARNING_FAILURE_LABEL_TEXT = """
OLD TOM DISTILLERY
Kentucky Straight Bourbon Whiskey
45% Alc./Vol. (90 Proof)
750 mL
Government Warning: Alcohol may be harmful.
"""


def load_application(name: str) -> dict:
    return json.loads((SAMPLES / "applications" / name).read_text())


def assert_valid_image(name: str) -> None:
    path = SAMPLES / "labels" / name
    assert path.exists()
    with Image.open(path) as image:
        image.verify()


def test_sample_label_images_are_valid_pngs():
    assert_valid_image("passing-bourbon-label.png")
    assert_valid_image("government-warning-failure-label.png")


def test_sample_passing_bourbon_scenario_passes():
    result = verify_application(PASSING_LABEL_TEXT, load_application("passing-bourbon.json"))
    assert result["overall_status"] == "PASS"


def test_sample_abv_mismatch_scenario_fails():
    result = verify_application(PASSING_LABEL_TEXT, load_application("abv-mismatch.json"))
    assert result["overall_status"] == "FAIL"
    assert any(field["field"] == "Alcohol Content" and field["status"] == "FAIL" for field in result["fields"])


def test_sample_government_warning_failure_scenario_fails():
    result = verify_application(WARNING_FAILURE_LABEL_TEXT, load_application("passing-bourbon.json"))
    assert result["overall_status"] == "FAIL"
    assert any(field["field"] == "Government Warning" and field["status"] == "FAIL" for field in result["fields"])
