import json

import pytest

from kindlepack.summary import SummaryValidationError, parse_summary_json, validate_summary_payload


def test_validates_loop_engineering_example():
    cues = validate_summary_payload(
        {
            "thesis": "Build systems that keep improving",
            "anchors": ["FIND", "ACT", "CHECK"],
            "descriptors": [
                "surface the next useful task",
                "execute with tools and context",
                "verify, store state, continue",
            ],
        }
    )

    assert cues.thesis == "Build systems that keep improving"
    assert cues.anchors == ("FIND", "ACT", "CHECK")


def test_parse_requires_strict_json_object():
    cues = parse_summary_json(
        json.dumps(
            {
                "thesis": "Use loops over one shot prompts",
                "anchors": ["PLAN", "ACT", "CHECK"],
                "descriptors": ["pick work", "use tools", "verify output"],
            }
        )
    )

    assert cues.anchors == ("PLAN", "ACT", "CHECK")


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"thesis": "one two three four five six seven eight nine ten eleven", "anchors": ["A", "B", "C"]}, "thesis"),
        ({"thesis": "short", "anchors": ["FIND", "FIND", "CHECK"]}, "distinct"),
        ({"thesis": "short", "anchors": ["find", "ACT", "CHECK"]}, "ALL CAPS"),
        ({"thesis": "short", "anchors": ["!!!", "ACT", "CHECK"]}, "1-2 words"),
        ({"thesis": "short", "anchors": ["TOO MANY WORDS", "ACT", "CHECK"]}, "1-2 words"),
        ({"thesis": "short", "anchors": ["ACT", "CHECK"]}, "exactly 3"),
    ],
)
def test_rejects_invalid_payloads(payload, message):
    with pytest.raises(SummaryValidationError, match=message):
        validate_summary_payload(payload)
