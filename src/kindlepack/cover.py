from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import textwrap

from PIL import Image, ImageDraw, ImageFont

from .summary import SummaryCues

CANVAS = (1600, 2560)
THUMB_WIDTH = 260

BG = (17, 19, 20)
INK = (246, 244, 238)
MUTED = (184, 183, 176)
DIM = (130, 132, 128)
RULE = (98, 99, 95)

DEFAULT_FONTS = (
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/SFNS.ttf",
)

SOURCE_GLYPHS = {
    "x": "X ARTICLE",
    "ghost": "GHOST",
    "research_pdf": "PDF",
    "web": "ARTICLE",
    "markdown": "MD",
}


class RenderNeedsShorterText(ValueError):
    """Raised when deterministic budget/floor checks fail."""


@dataclass(frozen=True)
class CoverMetadata:
    title: str
    author: str
    source_type: str
    date: str | None = None


@dataclass(frozen=True)
class CoverRenderResult:
    cover_path: Path
    thumbnail_path: Path
    font_fallback: bool
    warnings: tuple[str, ...] = ()


def render_cover(
    metadata: CoverMetadata,
    cues: SummaryCues,
    output_dir: str | Path,
    *,
    cover_font: str | None = None,
) -> CoverRenderResult:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    _validate_render_budget(metadata, cues)
    font_path, font_fallback = _resolve_font(cover_font)
    warnings: list[str] = []
    if font_fallback:
        warnings.append(f"cover_font unavailable; used {font_path}")

    img = Image.new("RGB", CANVAS, BG)
    draw = ImageDraw.Draw(img)
    margin = 136
    right = CANVAS[0] - margin

    header_label = _header_label(metadata)

    author_size = _fit_single(draw, metadata.author.upper(), font_path, 1000, 84, 62)
    _draw_text(draw, (margin, 168), metadata.author.upper(), font_path, author_size, MUTED)
    header_size = _fit_single(draw, header_label, font_path, 1000, 50, 42)
    _draw_text(draw, (margin, 280), header_label, font_path, header_size, MUTED)
    draw.line((margin, 380, right, 380), fill=RULE, width=4)

    title_lines = _wrap_title(draw, metadata.title, font_path, max_width=1160, max_lines=4)
    title_size = _fit_multiline(draw, title_lines, font_path, 1160, 580, 210, 108)
    y = 458
    for line in title_lines:
        _draw_text(draw, (margin, y), line.upper(), font_path, title_size, INK)
        y += int(title_size * 1.06)

    draw.line((margin, 1042, right, 1042), fill=RULE, width=5)
    thesis_lines = textwrap.wrap(cues.thesis, width=25)
    if len(thesis_lines) > 2:
        raise RenderNeedsShorterText("thesis wraps beyond two lines")
    thesis_size = _fit_multiline(draw, thesis_lines, font_path, 1328, 238, 106, 86)
    y = 1138
    for line in thesis_lines:
        _draw_text(draw, (margin, y), line, font_path, thesis_size, INK)
        y += int(thesis_size * 1.18)

    draw.line((margin, 1418, right, 1418), fill=RULE, width=4)

    row_y = [1510, 1810, 2110]
    for idx, (anchor, descriptor) in enumerate(zip(cues.anchors, cues.descriptors, strict=True)):
        y = row_y[idx]
        draw.line((margin, y - 42, right, y - 42), fill=(45, 47, 48), width=2)
        _draw_text(draw, (margin, y), f"0{idx + 1}", font_path, 48, DIM)
        anchor_size = _fit_single(draw, anchor, font_path, 940, 124, 78)
        _draw_text(draw, (margin + 180, y - 18), anchor, font_path, anchor_size, INK)
        if descriptor:
            descriptor_lines = _wrap_to_width(draw, descriptor, font_path, max_width=980, size=66, max_lines=2)
            descriptor_size = _fit_multiline(draw, descriptor_lines, font_path, 980, 138, 66, 52)
            descriptor_y = y + 118
            for line in descriptor_lines:
                _draw_text(draw, (margin + 184, descriptor_y), line, font_path, descriptor_size, MUTED)
                descriptor_y += int(descriptor_size * 1.12)

    draw.line((margin, 2382, right, 2382), fill=RULE, width=4)
    stem = _artifact_stem(metadata, cues)
    cover_path = output / f"{stem}.png"
    thumbnail_path = output / f"{stem}-thumb-260w.png"
    img.save(cover_path, quality=95)
    thumb_height = round(CANVAS[1] * THUMB_WIDTH / CANVAS[0])
    img.resize((THUMB_WIDTH, thumb_height), Image.Resampling.LANCZOS).save(thumbnail_path, quality=95)

    return CoverRenderResult(
        cover_path=cover_path,
        thumbnail_path=thumbnail_path,
        font_fallback=font_fallback,
        warnings=tuple(warnings),
    )


def _validate_render_budget(metadata: CoverMetadata, cues: SummaryCues) -> None:
    if len(metadata.title.strip()) > 90:
        raise RenderNeedsShorterText("title exceeds 90 characters")
    if len(metadata.author.strip()) > 48:
        raise RenderNeedsShorterText("author exceeds 48 characters")
    if len(_header_label(metadata)) > 42:
        raise RenderNeedsShorterText("source/date header exceeds 42 characters")
    for anchor in cues.anchors:
        if len(anchor) > 24:
            raise RenderNeedsShorterText(f"anchor too long for thumbnail budget: {anchor}")
    for descriptor in cues.descriptors:
        if len(descriptor) > 48:
            raise RenderNeedsShorterText("descriptor exceeds 48 characters")


def _resolve_font(configured: str | None) -> tuple[str, bool]:
    candidates = [configured] if configured else []
    candidates.extend(DEFAULT_FONTS)
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate, candidate != configured if configured else candidate != DEFAULT_FONTS[0]
    return "", True


def _font(path: str, size: int) -> ImageFont.ImageFont:
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def _draw_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, path: str, size: int, fill: tuple[int, int, int]) -> None:
    draw.text(xy, text, font=_font(path, size), fill=fill)


def _draw_text_right(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, path: str, size: int, fill: tuple[int, int, int]) -> None:
    fnt = _font(path, size)
    box = draw.textbbox((0, 0), text, font=fnt)
    draw.text((xy[0] - (box[2] - box[0]), xy[1]), text, font=fnt, fill=fill)


def _header_label(metadata: CoverMetadata) -> str:
    source = SOURCE_GLYPHS.get(metadata.source_type, metadata.source_type.upper())
    date = (metadata.date or "").strip()
    if not date:
        return source
    return f"{source} / {date.upper()}"


def _fit_single(draw: ImageDraw.ImageDraw, text: str, path: str, max_width: int, start: int, floor: int) -> int:
    for size in range(start, floor - 1, -4):
        box = draw.textbbox((0, 0), text, font=_font(path, size))
        if box[2] - box[0] <= max_width:
            return size
    raise RenderNeedsShorterText(f"text does not fit at floor size: {text}")


def _fit_multiline(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    path: str,
    max_width: int,
    max_height: int,
    start: int,
    floor: int,
) -> int:
    for size in range(start, floor - 1, -4):
        fnt = _font(path, size)
        widths = [draw.textbbox((0, 0), line, font=fnt)[2] for line in lines]
        height = len(lines) * int(size * 1.1)
        if max(widths, default=0) <= max_width and height <= max_height:
            return size
    raise RenderNeedsShorterText("multi-line text does not fit at floor size")


def _wrap_title(
    draw: ImageDraw.ImageDraw,
    title: str,
    path: str,
    *,
    max_width: int,
    max_lines: int,
) -> list[str]:
    words = title.strip().split()
    if not words:
        raise RenderNeedsShorterText("title is required")
    if len(words) == 1:
        return words

    lines: list[str] = []
    current: list[str] = []
    wrap_size = 150 if len(words) <= 3 else 110
    font = _font(path, wrap_size)
    for word in words:
        candidate = " ".join([*current, word])
        width = draw.textbbox((0, 0), candidate.upper(), font=font)[2]
        if width <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    if len(lines) > max_lines:
        raise RenderNeedsShorterText(f"title wraps beyond {max_lines} lines")
    return lines


def _wrap_to_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    path: str,
    *,
    max_width: int,
    size: int,
    max_lines: int,
) -> list[str]:
    words = text.strip().split()
    if not words:
        return []

    font = _font(path, size)
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        width = draw.textbbox((0, 0), candidate, font=font)[2]
        if width <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    if len(lines) > max_lines:
        raise RenderNeedsShorterText(f"text wraps beyond {max_lines} lines: {text}")
    return lines


def _artifact_stem(metadata: CoverMetadata, cues: SummaryCues) -> str:
    payload = json.dumps(
        {
            "title": metadata.title,
            "author": metadata.author,
            "source_type": metadata.source_type,
            "date": metadata.date,
            "thesis": cues.thesis,
            "anchors": cues.anchors,
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10]
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in metadata.title).strip("-")
    return f"{slug[:54].strip('-') or 'cover'}-{digest}"
