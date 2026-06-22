from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any


class SummaryValidationError(ValueError):
    """Raised when model-produced cover cues violate the strict contract."""


@dataclass(frozen=True)
class SummaryCues:
    thesis: str
    anchors: tuple[str, str, str]
    descriptors: tuple[str, str, str] = ("", "", "")


def parse_summary_json(text: str) -> SummaryCues:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SummaryValidationError(f"summary is not valid JSON: {exc}") from exc
    return validate_summary_payload(payload)


def validate_summary_payload(payload: dict[str, Any]) -> SummaryCues:
    if not isinstance(payload, dict):
        raise SummaryValidationError("summary payload must be an object")

    thesis = _required_string(payload, "thesis").strip()
    if not thesis:
        raise SummaryValidationError("thesis is required")
    if _word_count(thesis) > 10:
        raise SummaryValidationError("thesis must be 10 words or fewer")

    anchors_raw = payload.get("anchors")
    if not isinstance(anchors_raw, list) or len(anchors_raw) != 3:
        raise SummaryValidationError("anchors must contain exactly 3 items")
    anchors = tuple(_validate_anchor(anchor) for anchor in anchors_raw)
    normalized = [_normalize_anchor(anchor) for anchor in anchors]
    if len(set(normalized)) != 3:
        raise SummaryValidationError("anchors must be mutually distinct")

    descriptors_raw = payload.get("descriptors", ["", "", ""])
    if descriptors_raw is None:
        descriptors_raw = ["", "", ""]
    if not isinstance(descriptors_raw, list) or len(descriptors_raw) != 3:
        raise SummaryValidationError("descriptors must contain exactly 3 items when present")
    descriptors = tuple(_optional_string(item).strip() for item in descriptors_raw)

    return SummaryCues(thesis=thesis, anchors=anchors, descriptors=descriptors)


def reextract_request(error: Exception) -> dict[str, str]:
    return {
        "action": "re_extract_summary",
        "reason": str(error),
        "contract": (
            "Return strict JSON with thesis <=10 words, exactly 3 distinct ALL-CAPS "
            "anchors of 1-2 words each, and exactly 3 optional descriptors."
        ),
    }


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise SummaryValidationError(f"{key} must be a string")
    return value


def _optional_string(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise SummaryValidationError("descriptors must be strings")
    return value


def _validate_anchor(value: Any) -> str:
    if not isinstance(value, str):
        raise SummaryValidationError("anchors must be strings")
    anchor = " ".join(value.strip().split())
    if not anchor:
        raise SummaryValidationError("anchors cannot be empty")
    if anchor != anchor.upper():
        raise SummaryValidationError("anchors must be ALL CAPS")
    words = _word_count(anchor)
    if words < 1 or words > 2:
        raise SummaryValidationError("anchors must be 1-2 words each")
    return anchor


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", text))


def _normalize_anchor(anchor: str) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", anchor.upper()).strip()
