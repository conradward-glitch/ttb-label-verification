import re
from difflib import SequenceMatcher
from typing import Any

from .warning import validate_government_warning


MIN_REVIEW_SIMILARITY = 0.72
MIN_EVIDENCE_SIMILARITY = 0.55


def normalize_text(value: str) -> str:
    value = (value or "").replace("\u2019", "'").replace("\u2018", "'")
    value = value.lower()
    value = re.sub(r"&", " and ", value)
    value = re.sub(r"['’‘]", "", value)
    value = re.sub(r"[-–—_/]+", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _field_result(field: str, status: str, expected: str | None, found: str | None, message: str, evidence: str | None = None) -> dict[str, Any]:
    return {
        "field": field,
        "status": status,
        "expected": expected,
        "found": found,
        "message": message,
        "evidence": evidence,
    }


def _contains_normalized(ocr_text: str, expected: str) -> bool:
    normalized_expected = normalize_text(expected)
    normalized_ocr = normalize_text(ocr_text)
    return bool(normalized_expected and normalized_expected in normalized_ocr)


def _compact_alnum(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_text(value))


def _contains_compact_normalized(ocr_text: str, expected: str) -> bool:
    compact_expected = _compact_alnum(expected)
    compact_ocr = _compact_alnum(ocr_text)
    return bool(compact_expected and compact_expected in compact_ocr)


def _expected_token_evidence(ocr_text: str, expected: str) -> tuple[str, float]:
    normalized_ocr = normalize_text(ocr_text)
    compact_ocr = _compact_alnum(ocr_text)
    expected_tokens = [token for token in normalize_text(expected).split() if len(token) >= 3]
    if not expected_tokens:
        return "", 0.0

    matched: list[str] = []
    for token in expected_tokens:
        compact_token = _compact_alnum(token)
        if token in normalized_ocr or compact_token in compact_ocr:
            matched.append(token)
            continue
        if len(compact_token) >= 5 and any(
            SequenceMatcher(None, compact_token, compact_ocr[start:start + len(compact_token)]).ratio() >= 0.78
            for start in range(0, max(1, len(compact_ocr) - len(compact_token) + 1))
        ):
            matched.append(token)

    coverage = len(matched) / len(expected_tokens)
    return " ".join(matched), coverage


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()


def _best_line_match(ocr_text: str, expected: str) -> tuple[str, float]:
    lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
    if not lines:
        return "", 0.0
    scored = [(line, _similarity(line, expected)) for line in lines]
    return max(scored, key=lambda item: item[1])


def _verify_text_field(field: str, ocr_text: str, expected: str, fuzzy: bool = False) -> dict[str, Any]:
    if not expected:
        return _field_result(field, "REVIEW", expected, None, f"{field} was not supplied in the application data.")
    if not ocr_text.strip():
        return _field_result(field, "REVIEW", expected, None, f"OCR text is empty; {field} needs manual review.")
    if _contains_normalized(ocr_text, expected):
        return _field_result(field, "PASS", expected, expected, f"{field} appears on the label.", expected)
    if _contains_compact_normalized(ocr_text, expected):
        return _field_result(field, "PASS", expected, expected, f"{field} appears on the label after OCR spacing normalization.", expected)
    if fuzzy:
        found, score = _best_line_match(ocr_text, expected)
        if score >= 0.88:
            return _field_result(field, "PASS", expected, found, f"{field} matches after normalization/fuzzy comparison.", found)
        if score >= MIN_REVIEW_SIMILARITY:
            return _field_result(field, "REVIEW", expected, found, f"{field} may match but requires human review; similarity {score:.0%}.", found)
        token_evidence, token_coverage = _expected_token_evidence(ocr_text, expected)
        if token_coverage >= 0.66:
            return _field_result(field, "REVIEW", expected, token_evidence, f"{field} has OCR evidence across multiple lines and needs manual review.", token_evidence)
        if found and score >= MIN_EVIDENCE_SIMILARITY:
            return _field_result(field, "REVIEW", expected, found, f"{field} has weak OCR evidence and needs manual review; similarity {score:.0%}.", found)
    return _field_result(field, "FAIL", expected, None, f"{field} from application data was not found on the label.")


def extract_abv_values(text: str) -> list[float]:
    values: list[float] = []
    for match in re.finditer(r"(\d{1,3}(?:\.\d+)?)\s*%\s*(?:alc\.?/?vol\.?|abv|alcohol|)?", text, flags=re.I):
        value = float(match.group(1))
        if 0 < value <= 100:
            values.append(value)
    for match in re.finditer(r"(\d{1,3}(?:\.\d+)?)\s*proof", text, flags=re.I):
        proof = float(match.group(1))
        if 0 < proof <= 200:
            values.append(proof / 2)
    return values


def _verify_abv(ocr_text: str, expected: str) -> dict[str, Any]:
    expected_values = extract_abv_values(expected)
    found_values = extract_abv_values(ocr_text)
    if not expected_values:
        return _field_result("Alcohol Content", "REVIEW", expected, None, "Application alcohol content could not be parsed.")
    if not found_values:
        return _field_result("Alcohol Content", "FAIL", expected, None, "No alcohol content value was found on the label.")
    expected_abv = expected_values[0]
    for found in found_values:
        if abs(found - expected_abv) <= 0.1:
            return _field_result("Alcohol Content", "PASS", expected, f"{found:g}% ABV", "Alcohol content matches the application.", f"{found:g}% ABV")
    return _field_result("Alcohol Content", "FAIL", expected, ", ".join(f"{v:g}% ABV" for v in found_values), f"Alcohol content mismatch: expected {expected_abv:g}% ABV, found {', '.join(f'{v:g}% ABV' for v in found_values)}.")


def _normalize_net_contents_text(text: str) -> str:
    text = (text or "").lower()
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = re.sub(r"[-–—]+", " ", text)
    text = re.sub(r"(?<=\d)[oO](?=\s*(?:m\.?\s*l\.?|l\b|lit|oz|fl))", "0", text)
    text = re.sub(r"\bm\s*[\.]?\s*l\b\.?", " ml ", text)
    text = re.sub(r"\bf\s*l\s*[\.]?\s*o\s*z\b\.?", " fl oz ", text)
    text = re.sub(r"\bo\s*z\b\.?", " oz ", text)
    return re.sub(r"\s+", " ", text).strip()


def _net_contents_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    normalized = _normalize_net_contents_text(text)
    pattern = r"(\d+(?:[\.,]\d+)?)\s*(ml|milliliters?|l|liters?|litres?|ounces?|fl\s*oz|oz)\b"
    for match in re.finditer(pattern, normalized, flags=re.I):
        number = float(match.group(1).replace(",", "."))
        unit = re.sub(r"\s+", " ", match.group(2).lower())
        if unit in {"l", "liter", "liters", "litre", "litres"}:
            number *= 1000
            unit = "ml"
        elif unit in {"ml", "milliliter", "milliliters"}:
            unit = "ml"
        elif unit in {"oz", "ounce", "ounces", "fl oz"}:
            unit = "oz"
        tokens.append(f"{number:g} {unit}")
    return tokens


def _net_contents_evidence_lines(text: str) -> list[str]:
    evidence: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        normalized = _normalize_net_contents_text(stripped)
        if re.search(r"\d", normalized) and re.search(r"\b(?:m\s*l|ml|rn\s*l|l|liters?|litres?|ounces?|fl\s*oz|oz)\b", normalized, flags=re.I):
            evidence.append(stripped)
    return evidence


def _verify_net_contents(ocr_text: str, expected: str) -> dict[str, Any]:
    expected_tokens = _net_contents_tokens(expected)
    found_tokens = _net_contents_tokens(ocr_text)
    evidence_lines = _net_contents_evidence_lines(ocr_text)
    if not expected_tokens:
        return _field_result("Net Contents", "REVIEW", expected, None, "Application net contents could not be parsed.")
    for expected_token in expected_tokens:
        if expected_token in found_tokens:
            return _field_result("Net Contents", "PASS", expected, expected_token, "Net contents match the application.", expected_token)
    if found_tokens:
        return _field_result("Net Contents", "FAIL", expected, ", ".join(found_tokens), f"Net contents mismatch: expected {expected_tokens[0]}, found {', '.join(found_tokens)}.")
    if evidence_lines:
        evidence = "; ".join(evidence_lines)
        return _field_result("Net Contents", "REVIEW", expected, evidence, "Net contents evidence exists in OCR text but confidence is too weak; manual review required.", evidence)
    return _field_result("Net Contents", "FAIL", expected, None, "No net contents value was found on the label.")


def _verify_warning(ocr_text: str) -> dict[str, Any]:
    result = validate_government_warning(ocr_text)
    return _field_result("Government Warning", result.status, "Standard required warning", "Detected" if result.evidence else None, result.message, result.evidence)


def verify_application(ocr_text: str, application_data: dict[str, Any]) -> dict[str, Any]:
    fields = [
        _verify_text_field("Brand Name", ocr_text, application_data.get("brand_name", ""), fuzzy=True),
        _verify_text_field("Class/Type", ocr_text, application_data.get("class_type", ""), fuzzy=True),
        _verify_abv(ocr_text, application_data.get("alcohol_content", "")),
        _verify_net_contents(ocr_text, application_data.get("net_contents", "")),
        _verify_warning(ocr_text),
    ]
    statuses = [field["status"] for field in fields]
    if "FAIL" in statuses:
        overall = "FAIL"
        summary = "One or more required label checks failed. Review the failed fields before approval."
    elif "REVIEW" in statuses:
        overall = "REVIEW"
        summary = "No clear failures were found, but one or more fields need human review."
    else:
        overall = "PASS"
        summary = "All required MVP checks passed."
    return {"overall_status": overall, "summary": summary, "ocr_text": ocr_text, "fields": fields, "metadata": {"field_count": len(fields)}}
