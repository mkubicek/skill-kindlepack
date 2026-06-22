import json
from pathlib import Path

from kindlepack.deliver import deliver_to_harness
from kindlepack.state import RunRecord, append_run


def test_delivery_warning_shown_once(tmp_path: Path):
    prefs = tmp_path / "preferences.local.json"
    first = deliver_to_harness(file_path=tmp_path / "a.epub", kindle_address="k@example.com", preferences_path=prefs)
    second = deliver_to_harness(file_path=tmp_path / "a.epub", kindle_address="k@example.com", preferences_path=prefs)

    assert first.warning
    assert second.warning is None


def test_delivery_records_send_convention(tmp_path: Path):
    prefs = tmp_path / "preferences.local.json"
    sent = []

    def send(file_path: Path, kindle_address: str) -> None:
        sent.append((file_path, kindle_address))

    result = deliver_to_harness(
        file_path=tmp_path / "a.epub",
        kindle_address="k@example.com",
        preferences_path=prefs,
        send=send,
    )

    assert result.handed_to_mailer is True
    assert sent == [(tmp_path / "a.epub", "k@example.com")]
    assert json.loads(prefs.read_text())["send_convention"] == f"deliver {tmp_path / 'a.epub'} to k@example.com"


def test_append_run_jsonl(tmp_path: Path):
    ledger = tmp_path / "runs.jsonl"
    append_run(ledger, RunRecord(source_type="x", title="Title", output_path="out/title.epub"))

    row = json.loads(ledger.read_text().strip())
    assert row["source_type"] == "x"
    assert row["title"] == "Title"
    assert row["delivered"] is False
