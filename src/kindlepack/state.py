from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunRecord:
    source_type: str
    title: str
    output_path: str
    render_retries: int = 0
    font_fallback: bool = False
    delivered: bool = False
    notes: str = ""


def load_json(path: str | Path, default: Any) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text())


def save_json(path: str | Path, payload: Any) -> None:
    p = Path(path)
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def append_run(path: str | Path, record: RunRecord) -> None:
    payload = {"ts": datetime.now(timezone.utc).isoformat(), **asdict(record)}
    _append_jsonl(path, payload)


def append_correction(path: str | Path, *, what_was_wrong: str, the_fix: str, scope: str) -> None:
    if scope not in {"local", "generalizable"}:
        raise ValueError("scope must be local or generalizable")
    _append_jsonl(
        path,
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "what_was_wrong": what_was_wrong,
            "the_fix": the_fix,
            "scope": scope,
        },
    )


def mark_sender_warning_shown(preferences_path: str | Path) -> bool:
    prefs = load_json(preferences_path, {})
    already = bool(prefs.get("sender_approval_warning_shown"))
    if not already:
        prefs["sender_approval_warning_shown"] = True
        save_json(preferences_path, prefs)
    return already


def pr_suggestion_for_correction(*, what_was_wrong: str, the_fix: str) -> str:
    return (
        "Generalizable kindlepack correction suggestion\n\n"
        f"Problem: {what_was_wrong}\n\n"
        f"Proposed fix: {the_fix}\n\n"
        "Review this as a normal repository change before committing."
    )


def _append_jsonl(path: str | Path, payload: dict[str, Any]) -> None:
    p = Path(path)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")
