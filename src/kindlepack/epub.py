from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path
import zipfile

from ebooklib import epub

FIXED_MTIME = datetime(2000, 1, 1, tzinfo=timezone.utc)
FIXED_ZIP_DATE = (2000, 1, 1, 0, 0, 0)


def build_epub(
    *,
    title: str,
    author: str,
    body: str,
    cover_path: str | Path,
    output_path: str | Path,
    body_is_html: bool = False,
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    book = epub.EpubBook()
    book.set_identifier(_identifier(title, author))
    book.set_title(title)
    book.add_author(author)
    book.set_language("en")

    cover_bytes = Path(cover_path).read_bytes()
    book.set_cover("cover.png", cover_bytes)

    chapter = epub.EpubHtml(title=title, file_name="chapter.xhtml", lang="en")
    chapter.content = _body_html(title, author, body, body_is_html=body_is_html)
    book.add_item(chapter)

    style = epub.EpubItem(
        uid="style",
        file_name="styles/style.css",
        media_type="text/css",
        content=(
            "body{font-family:serif;line-height:1.5;margin:6%;}"
            "h1{font-size:1.7em;line-height:1.15;}"
            ".byline{font-style:italic;color:#555;}"
            "pre,code{font-family:monospace;white-space:pre-wrap;}"
            "blockquote{border-left:3px solid #999;margin-left:0;padding-left:1em;color:#333;}"
            "img{max-width:100%;height:auto;}"
        ),
    )
    book.add_item(style)
    chapter.add_item(style)

    book.toc = (epub.Link("chapter.xhtml", title, "chapter"),)
    book.spine = ["cover", chapter]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(str(output), book, {"mtime": FIXED_MTIME})
    _normalize_epub_zip(output)
    return output


def _body_html(title: str, author: str, body: str, *, body_is_html: bool) -> str:
    content = body if body_is_html else "<p>" + escape(body).replace("\n\n", "</p><p>").replace("\n", "<br/>") + "</p>"
    return f"<h1>{escape(title)}</h1><p class='byline'>{escape(author)}</p>{content}"


def _identifier(title: str, author: str) -> str:
    base = f"{title}:{author}".lower()
    return "kindlepack-" + "".join(ch if ch.isalnum() else "-" for ch in base).strip("-")[:96]


def _normalize_epub_zip(path: Path) -> None:
    normalized = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(path, "r") as src, zipfile.ZipFile(normalized, "w") as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            new_info = zipfile.ZipInfo(info.filename, date_time=FIXED_ZIP_DATE)
            new_info.compress_type = info.compress_type
            new_info.external_attr = info.external_attr
            new_info.comment = info.comment
            dst.writestr(new_info, data)
    normalized.replace(path)
