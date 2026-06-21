from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from markdown import markdown

from .cover import CoverMetadata, render_cover
from .deliver import DeliveryFunction, deliver_to_harness
from .epub import build_epub
from .pdf import prepend_cover_to_pdf
from .state import RunRecord, append_run
from .summary import SummaryCues

ARTICLE_TYPES = {"x", "ghost", "web", "markdown"}


@dataclass(frozen=True)
class PipelineInput:
    source_path: Path | None
    body: str | None
    title: str
    author: str
    source_type: str
    cues: SummaryCues
    date: str | None = None


def run_pipeline(
    item: PipelineInput,
    *,
    kindle_address: str,
    output_dir: str | Path = "out",
    cover_font: str | None = None,
    deliver: DeliveryFunction | None = None,
    runs_path: str | Path = "runs.jsonl",
) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    metadata = CoverMetadata(
        title=item.title,
        author=item.author,
        source_type=item.source_type,
        date=item.date,
    )
    cover = render_cover(metadata, item.cues, out / "covers", cover_font=cover_font)

    output_path = out / f"{_sanitize_title(item.title)}.{_extension(item)}"
    if _is_pdf(item):
        if item.source_path is None:
            raise ValueError("PDF branch requires source_path")
        output_path = _avoid_source_overwrite(output_path, item.source_path)
        prepend_cover_to_pdf(source_pdf=item.source_path, cover_path=cover.cover_path, output_path=output_path)
    elif item.source_type in ARTICLE_TYPES:
        if item.body is None:
            raise ValueError("article branch requires body text/html")
        body, body_is_html = _article_body(item)
        build_epub(
            title=item.title,
            author=item.author,
            body=body,
            cover_path=cover.cover_path,
            output_path=output_path,
            body_is_html=body_is_html,
        )
    else:
        raise ValueError(f"unsupported source_type: {item.source_type}")

    delivery = deliver_to_harness(file_path=output_path, kindle_address=kindle_address, send=deliver)
    append_run(
        runs_path,
        RunRecord(
            source_type=item.source_type,
            title=item.title,
            output_path=str(output_path),
            font_fallback=cover.font_fallback,
            delivered=delivery.handed_to_mailer,
            notes=delivery.warning or "",
        ),
    )
    return output_path


def _is_pdf(item: PipelineInput) -> bool:
    return item.source_type == "research_pdf" or bool(item.source_path and item.source_path.suffix.lower() == ".pdf")


def _extension(item: PipelineInput) -> str:
    return "pdf" if _is_pdf(item) else "epub"


def _sanitize_title(title: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in title).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "kindlepack"


def _avoid_source_overwrite(output_path: Path, source_path: Path) -> Path:
    output_resolved = output_path.resolve(strict=False)
    source_resolved = source_path.resolve(strict=False)
    if output_resolved != source_resolved:
        return output_path
    return output_path.with_name(f"{output_path.stem}-kindlepack{output_path.suffix}")


def _article_body(item: PipelineInput) -> tuple[str, bool]:
    if item.body is None:
        raise ValueError("article branch requires body text/html")
    if item.source_type == "markdown":
        return markdown(item.body, extensions=["extra", "sane_lists"]), True
    return item.body, item.source_type in {"web", "ghost"}
