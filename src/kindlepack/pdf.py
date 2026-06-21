from __future__ import annotations

from pathlib import Path
import tempfile

from PIL import Image
from pypdf import PdfReader, PdfWriter


def prepend_cover_to_pdf(
    *,
    source_pdf: str | Path,
    cover_path: str | Path,
    output_path: str | Path,
) -> Path:
    source = Path(source_pdf)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve(strict=False) == output.resolve(strict=False):
        raise ValueError("output_path must not overwrite source_pdf")

    reader = PdfReader(str(source))
    if not reader.pages:
        raise ValueError("source PDF has no pages")

    first = reader.pages[0]
    width = float(first.mediabox.width)
    height = float(first.mediabox.height)

    with tempfile.TemporaryDirectory() as tmpdir:
        cover_pdf = Path(tmpdir) / "cover.pdf"
        image = Image.open(cover_path).convert("RGB")
        image.save(cover_pdf, "PDF", resolution=300.0)
        cover_reader = PdfReader(str(cover_pdf))

        writer = PdfWriter()
        cover_page = writer.add_page(cover_reader.pages[0])
        cover_page.scale_to(width, height)
        for page in reader.pages:
            writer.add_page(page)
        with output.open("wb") as fh:
            writer.write(fh)

    return output
