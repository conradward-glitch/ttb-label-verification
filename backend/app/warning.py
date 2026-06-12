import re
from dataclasses import dataclass
from typing import Literal

Status = Literal["PASS", "FAIL", "REVIEW"]

REQUIRED_WARNING = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink "
    "alcoholic beverages during pregnancy because of the risk of birth defects. "
    "(2) Consumption of alcoholic beverages impairs your ability to drive a car or operate "
    "machinery, and may cause health problems."
)

WARNING_PARTS = [
    "according to the surgeon general",
    "women should not drink alcoholic beverages during pregnancy",
    "risk of birth defects",
    "consumption of alcoholic beverages impairs your ability to drive a car or operate machinery",
    "may cause health problems",
]


@dataclass
class WarningValidation:
    status: Status
    message: str
    evidence: str = ""


def _compact(text: str) -> str:
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = re.sub(r"\s+", " ", text.strip())
    return text


def _normalized(text: str) -> str:
    text = _compact(text).lower()
    text = re.sub(r"[^a-z0-9:()]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def validate_government_warning(ocr_text: str) -> WarningValidation:
    compact = _compact(ocr_text)
    if not compact:
        return WarningValidation("REVIEW", "No OCR text was extracted, so the government warning needs manual review.")

    if "GOVERNMENT WARNING:" not in compact:
        lowered = compact.lower()
        if "government warning" in lowered:
            return WarningValidation("FAIL", "Government warning prefix must be all caps as 'GOVERNMENT WARNING:'.")
        return WarningValidation("FAIL", "Required government warning was not found on the label.")

    normalized = _normalized(compact)
    positions: list[int] = []
    for part in WARNING_PARTS:
        idx = normalized.find(part)
        if idx == -1:
            return WarningValidation("FAIL", f"Government warning is missing or materially alters required phrase: '{part}'.")
        positions.append(idx)

    if positions != sorted(positions):
        return WarningValidation("FAIL", "Government warning phrases are present but not in the required order.")

    start = compact.find("GOVERNMENT WARNING:")
    evidence = compact[start:start + 360] if start >= 0 else ""
    return WarningValidation("PASS", "Government warning text is present with required all-caps prefix and required wording.", evidence)
