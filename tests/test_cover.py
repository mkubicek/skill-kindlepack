from pathlib import Path

import pytest
from PIL import Image

from kindlepack.cover import CoverMetadata, RenderNeedsShorterText, _header_label, render_cover
from kindlepack.summary import SummaryCues


def test_render_cover_emits_png_and_thumbnail(tmp_path: Path):
    result = render_cover(
        CoverMetadata(title="Loop Engineering", author="Addy Osmani", source_type="x"),
        SummaryCues(
            thesis="Build systems that keep improving",
            anchors=("EVAL LOOPS", "TOOL CONTEXT", "VERIFIED STATE"),
            descriptors=(
                "measure, improve, repeat",
                "agents need state and tools",
                "prove each iteration worked",
            ),
        ),
        tmp_path,
    )

    assert result.cover_path.exists()
    assert _header_label(CoverMetadata(title="Loop Engineering", author="Addy Osmani", source_type="x", date="June 7, 2026")) == "X ARTICLE / JUNE 7, 2026"
    assert result.thumbnail_path.exists()
    assert Image.open(result.cover_path).size == (1600, 2560)
    assert Image.open(result.thumbnail_path).size == (260, 416)


def test_render_fails_when_anchor_exceeds_budget(tmp_path: Path):
    with pytest.raises(RenderNeedsShorterText, match="anchor too long"):
        render_cover(
            CoverMetadata(title="Readable Cover", author="Milan", source_type="web"),
            SummaryCues(
                thesis="Make covers readable",
                anchors=("THIS ANCHOR IS FAR TOO HUGE", "ACT", "CHECK"),
                descriptors=("", "", ""),
            ),
            tmp_path,
        )


def test_render_allows_three_line_titles(tmp_path: Path):
    result = render_cover(
        CoverMetadata(title="Designing Useful Feedback Loops for Agents", author="Milan", source_type="web"),
        SummaryCues(thesis="Make agent work inspectable", anchors=("EVAL LOOPS", "TOOL CONTEXT", "STATE")),
        tmp_path,
    )

    assert result.cover_path.exists()


def test_missing_configured_font_records_warning(tmp_path: Path):
    result = render_cover(
        CoverMetadata(title="Loop Engineering", author="Addy Osmani", source_type="x"),
        SummaryCues(thesis="Build systems that keep improving", anchors=("EVAL LOOPS", "TOOL CONTEXT", "STATE")),
        tmp_path,
        cover_font="/missing/font.ttf",
    )

    assert result.font_fallback is True
    assert result.warnings


def test_render_accepts_publish_date_in_header(tmp_path: Path):
    result = render_cover(
        CoverMetadata(title="Loop Engineering", author="Addy Osmani", source_type="x", date="June 7, 2026"),
        SummaryCues(thesis="Build systems that keep improving", anchors=("EVAL LOOPS", "TOOL CONTEXT", "STATE")),
        tmp_path,
    )

    assert result.cover_path.exists()


def test_render_fails_when_source_date_header_exceeds_budget(tmp_path: Path):
    with pytest.raises(RenderNeedsShorterText, match="source/date header"):
        render_cover(
            CoverMetadata(
                title="Readable Cover",
                author="Milan",
                source_type="research_pdf",
                date="A very long publication date string that will not fit",
            ),
            SummaryCues(thesis="Make covers readable", anchors=("READ", "MARK", "ACT")),
            tmp_path,
        )
