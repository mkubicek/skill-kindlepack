# skill-kindlepack

`skill-kindlepack` packages one article or research PDF into a Kindle-ready reading product:

- a clean EPUB for article/text sources
- a PDF passthrough with a deterministic cover prepended for research PDFs
- a thumbnail-legible Pillow cover
- local run state and a thin delivery seam for the harness mailer

It is a reading-product packaging skill, not an image-generation skill. Covers are deterministic Pillow renders and should work first in the Kindle library thumbnail.

## Setup

```bash
uv sync
cp config.example.json config.local.json
```

Edit `config.local.json` locally:

```json
{
  "kindle_address": "your-kindle-address@example.com",
  "cover_font": "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
}
```

`config.local.json`, preferences, ledgers, corrections, and output artifacts are gitignored.

## Kindle Sender Approval

Before the first send, approve the harness sender address in Amazon's Personal Document Settings. This package does not inspect the inbox and cannot detect Kindle rejection emails.

## Development

```bash
uv run pytest
```

Core contracts:

- summary cues are strict JSON with one thesis and three ALL-CAPS anchors
- the cover canvas is fixed at `1600 x 2560`
- every render emits a `260px` thumbnail
- EPUB/PDF assembly is deterministic for the same inputs on the same machine
- delivery is delegated to the harness; no SMTP client is included
