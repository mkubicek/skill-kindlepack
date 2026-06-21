---
name: kindlepack
description: "Package one article or research PDF into a Kindle-ready EPUB/PDF with a deterministic thumbnail-legible cover."
---

# Kindlepack

Use when packaging a single article, X/Ghost capture, markdown/web text, or research PDF for Kindle with a consistent reading experience.

## Workflow

1. Resolve exactly one source document and metadata: `title`, `author`, `source_type`, optional `date`.
2. Extract cover cues as strict JSON:
   `{"thesis": str, "anchors": [str, str, str], "descriptors": [str, str, str]}`.
3. Validate cues before rendering:
   - thesis: 10 words or fewer
   - anchors: exactly 3, ALL CAPS, mutually distinct, 1-2 words each
   - descriptors: optional, one short phrase per anchor
4. Route by source:
   - `x`, `ghost`, `web`, `markdown` -> clean reflowable EPUB
   - `research_pdf` or `.pdf` -> PDF passthrough with the cover prepended as page 1
5. Render cover with Pillow only. No AI image generation, no browser renderer, no vendored fonts.
6. Require the 260px-wide thumbnail artifact; if the title, thesis, or anchors overflow their boxes, request shorter cues and retry.
7. Hand the finished file to the harness mailer for `kindle_address`. Do not implement SMTP and do not claim Kindle inbox rejection checks.
8. Append `runs.jsonl` and keep local preferences/corrections out of git.

## Few-Shot Cue Example

For "Loop Engineering" by Addy Osmani:

```json
{
  "thesis": "Build systems that keep improving",
  "anchors": ["EVAL LOOPS", "TOOL CONTEXT", "VERIFIED STATE"],
  "descriptors": [
    "measure, improve, repeat",
    "agents need state and tools",
    "prove each iteration worked"
  ]
}
```

## First Run

Warn once that the sender email must be approved in Amazon Personal Document Settings. Store `sender_approval_warning_shown` in `preferences.local.json`.
