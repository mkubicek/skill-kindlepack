from pathlib import Path

import pytest
from PIL import Image

from kindlepack.cover import CoverMetadata, RenderNeedsShorterText, _header_label, render_cover
from kindlepack.summary import SummaryCues


def _non_background_pixels(image: Image.Image, bg: tuple[int, int, int] = (17, 19, 20)) -> int:
    pixels = image.load()
    width, height = image.size
    count = 0
    for y in range(height):
        for x in range(width):
            if pixels[x, y] != bg:
                count += 1
    return count


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


def test_header_keeps_source_date_out_of_kindle_badge_corner(tmp_path: Path):
    result = render_cover(
        CoverMetadata(title="Loop Engineering", author="Addy Osmani", source_type="x", date="June 7, 2026"),
        SummaryCues(thesis="Build systems that keep improving", anchors=("EVAL LOOPS", "TOOL CONTEXT", "STATE")),
        tmp_path,
    )

    image = Image.open(result.cover_path)
    top_right_badge_zone = image.crop((1080, 120, 1600, 340))
    assert _non_background_pixels(top_right_badge_zone) == 0


def test_descriptor_text_uses_lower_section_space(tmp_path: Path):
    result = render_cover(
        CoverMetadata(title="Loop Engineering", author="Addy Osmani", source_type="x", date="June 7, 2026"),
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

    image = Image.open(result.cover_path)
    lower_summary_zone = image.crop((300, 1625, 1280, 2310))
    assert _non_background_pixels(lower_summary_zone) > 24_000


def test_dynamic_layout_keeps_right_edge_clear_and_fills_safe_height(tmp_path: Path):
    result = render_cover(
        CoverMetadata(title="Loop Engineering", author="Addy Osmani", source_type="x", date="June 7, 2026"),
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

    image = Image.open(result.cover_path)
    right_edge = image.crop((1498, 0, 1600, 2560))
    summary_safe_zone = image.crop((104, 1280, 1496, 2360))
    assert _non_background_pixels(right_edge) == 0
    assert _non_background_pixels(summary_safe_zone) > 200_000


def test_render_fails_when_anchor_exceeds_budget(tmp_path: Path):
    with pytest.raises(RenderNeedsShorterText, match="anchor too long"):
        render_cover(
            CoverMetadata(title="Readable Cover", author="Test Author", source_type="web"),
            SummaryCues(
                thesis="Make covers readable",
                anchors=("THIS ANCHOR IS FAR TOO HUGE", "ACT", "CHECK"),
                descriptors=("", "", ""),
            ),
            tmp_path,
        )


def test_render_allows_three_line_titles(tmp_path: Path):
    result = render_cover(
        CoverMetadata(title="Designing Useful Feedback Loops for Agents", author="Test Author", source_type="web"),
        SummaryCues(thesis="Make agent work inspectable", anchors=("EVAL LOOPS", "TOOL CONTEXT", "STATE")),
        tmp_path,
    )

    assert result.cover_path.exists()


def test_long_valid_cover_fits_anchor_and_descriptor_together(tmp_path: Path):
    result = render_cover(
        CoverMetadata(title="Designing Useful Feedback Loops for Practical Agentic Systems", author="Test Author", source_type="web"),
        SummaryCues(
            thesis="Make agent work inspectable and repeatable",
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
                author="Test Author",
                source_type="research_pdf",
                date="A very long publication date string that will not fit",
            ),
            SummaryCues(thesis="Make covers readable", anchors=("READ", "MARK", "ACT")),
            tmp_path,
        )
