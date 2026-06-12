from pydantic import BaseModel, Field
from typing import Any, Literal

Status = Literal["PASS", "FAIL", "REVIEW"]


class OcrResult(BaseModel):
    text: str = ""
    status: Status = "PASS"
    message: str = ""


class FieldResult(BaseModel):
    field: str
    status: Status
    expected: str | None = None
    found: str | None = None
    message: str
    evidence: str | None = None


class VerificationResponse(BaseModel):
    overall_status: Status
    summary: str
    ocr_text: str
    fields: list[FieldResult]
    metadata: dict[str, Any] = Field(default_factory=dict)
