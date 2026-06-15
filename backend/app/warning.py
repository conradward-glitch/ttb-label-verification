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


WARNING_ANCHORS = [
    "government warn",
    "surgeon",
    "women",
    "pregnancy",
    "birth defects",
    "consumption",
    "drive",
    "operate machinery",
    "health problems",
]


def _anchor_count(normalized: str) -> int:
    return sum(1 for anchor in WARNING_ANCHORS if anchor in normalized)


def _warning_evidence(compact: str) -> str:
    upper_start = compact.find("GOVERNMENT WARNING")
    if upper_start >= 0:
        return compact[upper_start:upper_start + 360]
    lowered = compact.lower()
    warning_start = lowered.find("government warn")
    if warning_start >= 0:
        return compact[warning_start:warning_start + 360]
    return compact[:360]


def validate_government_warning(ocr_text: str) -> WarningValidation:
    compact = _compact(ocr_text)
    if not compact:
        return WarningValidation("REVIEW", "No OCR text was extracted, so the government warning needs manual review.")

    normalized = _normalized(compact)

    if "GOVERNMENT WARNING:" not in compact:
        lowered = compact.lower()
        if "government warning" in lowered:
            return WarningValidation("FAIL", "Government warning prefix must be all caps as 'GOVERNMENT WARNING:'.")
        if _anchor_count(normalized) >= 3:
            return WarningValidation(
                "REVIEW",
                "Warning-like OCR text was detected, but the required government warning could not be confirmed exactly. Manual review is required.",
                _warning_evidence(compact),
            )
        return WarningValidation("FAIL", "Required government warning was not found on the label.")

    positions: list[int] = []
    missing_parts: list[str] = []
    for part in WARNING_PARTS:
        idx = normalized.find(part)
        if idx == -1:
            missing_parts.append(part)
        else:
            positions.append(idx)

    if missing_parts:
        found_count = len(WARNING_PARTS) - len(missing_parts)
        later_warning_language_present = "consumption" in normalized and "health problems" in normalized
        if later_warning_language_present:
            return WarningValidation("FAIL", f"Government warning is missing or materially alters required phrase: '{missing_parts[0]}'.")
        if found_count >= 2 and _anchor_count(normalized) >= 4:
            return WarningValidation(
                "REVIEW",
                "Partial government warning text was detected, but OCR or the uploaded label panel may not show the full required warning. Manual review is required.",
                _warning_evidence(compact),
            )
        return WarningValidation("FAIL", f"Government warning is missing or materially alters required phrase: '{missing_parts[0]}'.")

    if positions != sorted(positions):
        return WarningValidation("FAIL", "Government warning phrases are present but not in the required order.")

    start = compact.find("GOVERNMENT WARNING:")
    evidence = compact[start:start + 360] if start >= 0 else ""
    return WarningValidation("PASS", "Government warning text is present with required all-caps prefix and required wording.", evidence)
