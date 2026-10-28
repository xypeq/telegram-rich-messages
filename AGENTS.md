# Guide for AI assistants

You were probably given this repo to add Telegram **Rich Messages** (and
maybe ephemeral messages) to someone's bot. This file is the plan. The
facts live in `docs/`.

## Read first

1. [docs/html-reference.md](docs/html-reference.md) — the complete list of
   supported tags and attributes, limits, Markdown syntax. Anything not
   there is not supported.
2. [docs/api.md](docs/api.md) — the methods (`sendRichMessage`,
   `sendRichMessageDraft`, `editMessageText` with `rich_message`, media
   uploads, ephemeral send/edit/delete, callback answers) and real error
   codes.
3. [docs/behavior.md](docs/behavior.md) — what the apps actually render.
   Read it before designing layouts or LaTeX; several things the API
   accepts don't display (or display differently on phone vs desktop).
4. [rich_messages.py](rich_messages.py) — a working Python implementation.
   Copy it into a Python bot, or use it as the reference when porting.

## Implementing in the user's bot

1. **Check the bot's stack.** Rich messages are new (Bot API 10.1, June
   2026). Most Telegram libraries don't wrap `sendRichMessage` yet. If the
   library has no method for it, call the Bot API directly over HTTPS
   (`POST /bot<TOKEN>/sendRichMessage`, JSON body) with the HTTP client the
   bot already uses. Most libraries also have a raw "call any method" escape
   hatch.
2. **Add a small helper layer** that builds the HTML (escaping text!) and
   sends it. In Python, `rich_messages.py` *is* that layer. In other
   languages, port the parts you need: escaping, the tag builders, the
   multipart upload path, and error handling.
3. **Escape every piece of user or dynamic text** (`&`, `<`, `>`, `"`)
   before putting it into HTML, including inside `<tg-math>`.
4. **Uploads** use `rich_message.media` + `tg://photo|video|audio|document?id=`
   links, sent as `multipart/form-data` (see docs/api.md → Media uploads).
   Plain `http(s)` URLs in `src` need no upload.
5. **Buttons:** `<tg-button type="callback_data" data="…">` presses arrive
   as normal `callback_query` updates. Hook them into the bot's existing
   update handler (never start a second `getUpdates` poller: Telegram
   allows one, the second gets 409). Always `answerCallbackQuery`. Update
   the message with `editMessageText` + `rich_message`.
6. **Ephemeral messages:** `sendRichMessage` with
   `ephemeral_message_parameters: {receiver_user_id, callback_query_id}`.
   Store the returned `ephemeral_message_id` to edit or delete it later.
   Presses inside it come with `message.ephemeral_message_id`.
7. **Respect the limits:** 32768 chars, 500 blocks, 16 nesting levels, 50
   media, 20 table columns, 8 buttons per row, `callback_data` 1–64 bytes,
   callback answer text ≤ 200 chars.
8. **Handle errors:** read `description` (e.g. `RICH_MESSAGE_EMPTY`) and
   wait out HTTP 429 `retry_after`.

## Layout rules that save time

- Only `<br>` breaks a line; source newlines are spaces.
- For blank space use `<p>&#x2800;</p>`; `<p> </p>` is rejected.
- Table cells take inline content only. Links in a table with fewer than 2
  rows aren't tappable.
- Use `align="center"` on `<tg-button-row>` unless you want buttons
  stretched full width. Keep labels short for phones.
- Keep media at most 5:1 wide; upload GIFs as `video`, or better a silent
  MP4 as `animation`.
- LaTeX: no colors, no `\\` (blank on phone), no `\rule` (blank on
  desktop), keep formulas narrower than a phone screen. Stack lines with
  `\underset` / `\atop`.

## Verifying

The API accepts many things that apps then render badly or not at all
(especially LaTeX). After sending, ask the user to check on **both** phone
and desktop instead of assuming it looks right.
