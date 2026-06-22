from pathlib import Path
import time

from PIL import Image
import pytest
from pypdf import PdfReader, PdfWriter

from kindlepack.epub import build_epub
from kindlepack.pdf import prepend_cover_to_pdf


def _cover(path: Path) -> Path:
    Image.new("RGB", (1600, 2560), (17, 19, 20)).save(path)
    return path


def test_build_epub_embeds_cover(tmp_path: Path):
    cover = _cover(tmp_path / "cover.png")
    output = build_epub(
        title="Loop Engineering",
        author="Addy Osmani",
        body="Body text",
        cover_path=cover,
        output_path=tmp_path / "loop.epub",
    )

    assert output.exists()
    assert output.stat().st_size > 0


def test_build_epub_is_deterministic_for_same_inputs(tmp_path: Path):
    cover = _cover(tmp_path / "cover.png")
    first = build_epub(
        title="Loop Engineering",
        author="Addy Osmani",
        body="Body text",
        cover_path=cover,
        output_path=tmp_path / "first.epub",
    )
    time.sleep(3)
    second = build_epub(
        title="Loop Engineering",
        author="Addy Osmani",
        body="Body text",
        cover_path=cover,
        output_path=tmp_path / "second.epub",
    )

    assert first.read_bytes() == second.read_bytes()


def test_prepend_cover_to_pdf_adds_one_page(tmp_path: Path):
    source = tmp_path / "source.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=400, height=600)
    with source.open("wb") as fh:
        writer.write(fh)

    output = prepend_cover_to_pdf(
        source_pdf=source,
        cover_path=_cover(tmp_path / "cover.png"),
        output_path=tmp_path / "output.pdf",
    )

    reader = PdfReader(str(output))
    assert len(reader.pages) == 2
    assert float(reader.pages[0].mediabox.width) == 400
    assert float(reader.pages[0].mediabox.height) == 600


def test_prepend_cover_to_pdf_rejects_source_overwrite(tmp_path: Path):
    source = tmp_path / "source.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=400, height=600)
    with source.open("wb") as fh:
        writer.write(fh)
    original_bytes = source.read_bytes()

    with pytest.raises(ValueError, match="must not overwrite"):
        prepend_cover_to_pdf(
            source_pdf=source,
            cover_path=_cover(tmp_path / "cover.png"),
            output_path=source,
        )

    assert source.read_bytes() == original_bytes
