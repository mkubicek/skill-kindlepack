from pathlib import Path

import pytest
from PIL import Image

from kindlepack.cover import CoverMetadata, RenderNeedsShorterText, render_cover
from kindlepack.summary import SummaryCues


def test_render_cover_emits_png_and_thumbnail(tmp_path: Path):
    result = render_cover(
        CoverMetadata(title="Loop Engineering", author="Addy Osmani", source_type="x"),
        SummaryCues(
            thesis="Build systems that keep improving",
            anchors=("FIND", "ACT", "CHECK"),
            descriptors=(
                "surface the next useful task",
                "execute with tools and context",
                "verify, store state, continue",
            ),
        ),
        tmp_path,
    )

    assert result.cover_path.exists()
    assert result.thumbnail_path.exists()
    assert Image.open(result.cover_path).size == (1600, 2560)
    assert Image.open(result.thumbnail_path).size == (260, 416)


def test_render_fails_when_anchor_exceeds_budget(tmp_path: Path):
    with pytest.raises(RenderNeedsShorterText, match="anchor too long"):
        render_cover(
            CoverMetadata(title="Readable Cover", author="Milan", source_type="web"),
            SummaryCues(
                thesis="Make covers readable",
                anchors=("THIS ANCHOR IS HUGE", "ACT", "CHECK"),
                descriptors=("", "", ""),
            ),
            tmp_path,
        )


def test_render_allows_three_line_titles(tmp_path: Path):
    result = render_cover(
        CoverMetadata(title="Designing Useful Feedback Loops for Agents", author="Milan", source_type="web"),
        SummaryCues(thesis="Make agent work inspectable", anchors=("FIND", "ACT", "CHECK")),
        tmp_path,
    )

    assert result.cover_path.exists()


def test_missing_configured_font_records_warning(tmp_path: Path):
    result = render_cover(
        CoverMetadata(title="Loop Engineering", author="Addy Osmani", source_type="x"),
        SummaryCues(thesis="Build systems that keep improving", anchors=("FIND", "ACT", "CHECK")),
        tmp_path,
        cover_font="/missing/font.ttf",
    )

    assert result.font_fallback is True
    assert result.warnings
