from pathlib import Path

from ebooklib import ITEM_DOCUMENT, epub
from pypdf import PdfWriter

from kindlepack.pipeline import PipelineInput, run_pipeline
from kindlepack.summary import SummaryCues


def test_pdf_pipeline_never_overwrites_source_with_matching_title(tmp_path: Path):
    source = tmp_path / "report.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=400, height=600)
    with source.open("wb") as fh:
        writer.write(fh)
    original_bytes = source.read_bytes()

    output = run_pipeline(
        PipelineInput(
            source_path=source,
            body=None,
            title="Report",
            author="Research Team",
            source_type="research_pdf",
            cues=SummaryCues(thesis="Understand the report", anchors=("READ", "MARK", "ACT")),
        ),
        kindle_address="kindle@example.com",
        output_dir=tmp_path,
        runs_path=tmp_path / "runs.jsonl",
    )

    assert output == tmp_path / "report-kindlepack.pdf"
    assert output.exists()
    assert source.read_bytes() == original_bytes


def test_markdown_pipeline_renders_markdown_to_html(tmp_path: Path):
    output = run_pipeline(
        PipelineInput(
            source_path=None,
            body="# Heading\n\n- one\n- two",
            title="Markdown Report",
            author="Writer",
            source_type="markdown",
            cues=SummaryCues(thesis="Read the markdown report", anchors=("READ", "LIST", "ACT")),
        ),
        kindle_address="kindle@example.com",
        output_dir=tmp_path,
        runs_path=tmp_path / "runs.jsonl",
    )

    book = epub.read_epub(str(output))
    docs = [item.get_content().decode("utf-8") for item in book.get_items_of_type(ITEM_DOCUMENT)]
    chapter = "\n".join(docs)
    assert "<h1>Heading</h1>" in chapter
    assert "<li>one</li>" in chapter
    assert "# Heading" not in chapter
