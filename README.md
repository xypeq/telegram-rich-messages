# telegram-rich-messages

A practical guide and a small Python library for Telegram's **Rich
Messages** (Bot API 10.1–10.3): bot messages with headings, tables,
formulas, maps, collages, slideshows, collapsible sections, footnotes,
uploaded media and buttons *inside* the message, plus **ephemeral
messages** only one user sees.

The official docs list the tags. This repo adds what you only learn by
sending real messages: what each app actually renders, the hidden limits,
and the errors you'll hit. Everything in [docs/behavior.md](docs/behavior.md)
was tested live.

> **Using an AI assistant?** Give it this repo's link and say "implement
> rich messages in my bot". [AGENTS.md](AGENTS.md) tells it what to read
> and how to do it, in any language.

## What a rich message is

One HTML (or Markdown) string sent as `rich_message` to `sendRichMessage`:

```http
POST https://api.telegram.org/bot<TOKEN>/sendRichMessage
{
  "chat_id": -1001234567890,
  "rich_message": {
    "html": "<h1>Release 2.0</h1><p>Now with <b>tables</b>:</p><table bordered><tr><th>Plan</th><th>Price</th></tr><tr><td>Pro</td><td>$5</td></tr></table><tg-button-row align=\"center\"><tg-button type=\"url\" style=\"primary\" url=\"https://example.com\">Upgrade</tg-button></tg-button-row>"
  }
}
```

No library needed — any HTTP client works. The Python helper just makes
the HTML easier to build.

## Python quickstart

`rich_messages.py` is a single file with one dependency:

```bash
pip install httpx
```

```python
import asyncio
from rich_messages import RM, RichMessage

async def main():
    rm = RichMessage(BOT_TOKEN)
    banner = rm.attach_media("banner", open("banner.mp4", "rb"), "animation")  # upload
    rm.html(
        RM.video(banner)
        + RM.heading("Release 2.0", 1)
        + RM.paragraph("Now with " + RM.bold("tables") + " and " + RM.math(r"e^{i\pi}+1=0"))
        + RM.table([
            RM.table_row([RM.table_cell("Plan", header=True), RM.table_cell("Price", header=True)]),
            RM.table_row([RM.table_cell("Pro"), RM.table_cell("$5")]),
        ], bordered=True)
        + RM.button_row([RM.button("Upgrade", url="https://example.com", style="primary")],
                        align="center")
    )
    await rm.send(CHAT_ID)

asyncio.run(main())
```

`RM` helpers return HTML strings and nest freely; they don't escape text,
so wrap untrusted input in `RM.text(...)`. `RichMessage` also does
`.edit()`, `.send_draft()` (streaming), and ephemeral messages
(`send(..., ephemeral_to=user_id)`, `.edit_ephemeral()`,
`RichMessage.delete_ephemeral()`).

## Features at a glance

| Feature | Tag |
|---|---|
| Headings, paragraphs, small text, dividers | `<h1>`–`<h6>`, `<p>`, `<footer>`, `<hr/>` |
| Bold, italic, underline, strike, code, highlight, sub/sup, spoiler | `<b> <i> <u> <s> <code> <mark> <sub> <sup> <tg-spoiler>` |
| Links, mentions, anchors, footnote popups | `<a>`, `<tg-reference>` |
| Dates in the reader's time zone | `<tg-time>` |
| LaTeX formulas | `<tg-math>`, `<tg-math-block>` |
| Lists, numbered lists, checklists | `<ul> <ol> <li>`, `<input type="checkbox">` |
| Quotes, expandable quotes, pull quotes | `<blockquote [expandable]>`, `<aside>` |
| Collapsible sections | `<details><summary>` |
| Tables (borders, stripes, compact, spans, alignment) | `<table>` |
| Photos, videos, GIFs, audio, voice, files, captions, spoilers | `<img> <video> <audio> <tg-document> <figure>` |
| Grids and swipeable galleries | `<tg-collage>`, `<tg-slideshow>` |
| Maps | `<tg-map>` |
| Buttons in rows or inline in text | `<tg-button-row>`, `<tg-button>` |
| "Thinking…" block while streaming | `<tg-thinking>` |

## Docs

- [docs/html-reference.md](docs/html-reference.md): every tag and attribute, limits, Markdown syntax
- [docs/api.md](docs/api.md): sending, streaming, editing, uploads, ephemeral messages, button presses, error codes
- [docs/behavior.md](docs/behavior.md): what phone and desktop apps really do (tables, buttons, media sizes, LaTeX quirks, rate limits)
- [examples/](examples/): a full showcase message, and an interactive ephemeral panel

## Status

Built against Bot API 10.3 (August 2026). Behavior notes come from one
phone and one desktop client in October 2026; apps change, so treat them as
observations, not guarantees. Corrections welcome.

## License

MIT
