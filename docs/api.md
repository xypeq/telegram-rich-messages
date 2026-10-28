# API methods

How rich messages move through the Bot API: sending, streaming, editing,
uploading media, ephemeral messages and button presses. Plain HTTPS +
JSON, so this works from any language. Python equivalents from
`rich_messages.py` are noted.

All methods: `POST https://api.telegram.org/bot<TOKEN>/<method>` with a
JSON body. Replies are `{"ok": true, "result": …}` or `{"ok": false,
"error_code": …, "description": "…", "parameters": {"retry_after": …}}`.

## InputRichMessage

The object every method below takes as `rich_message`. Use **exactly one**
of `html`, `markdown`, `blocks`.

| Field | Type | Meaning |
|---|---|---|
| `html` | string | Rich HTML ([html-reference.md](html-reference.md)) |
| `markdown` | string | Rich Markdown |
| `blocks` | array | `InputRichBlock*` objects (alternative to the strings) |
| `media` | array of `InputRichMessageMedia` | media referenced by `tg://…?id=` links in html/markdown |
| `is_rtl` | bool | show right-to-left |
| `skip_entity_detection` | bool | don't auto-link URLs, @mentions, #tags, phones… |

Python: `RichMessage(token).html(text, is_rtl=…, skip_entity_detection=…)`,
`.payload()` returns this object.

## sendRichMessage

Sends a rich message; returns the `Message`.

```json
{"chat_id": -1001234567890, "rich_message": {"html": "<h1>Hi</h1><p>text</p>"}}
```

Takes the usual send parameters too: `message_thread_id`,
`reply_parameters`, `reply_markup` (a classic inline keyboard still works
alongside in-message buttons), `disable_notification`, `protect_content`,
`message_effect_id`, `business_connection_id`, `allow_paid_broadcast`,
`direct_messages_topic_id`, `suggested_post_parameters`,
`ephemeral_message_parameters`.

The bot needs the right to send media in that chat if the message has any.

Python: `await RichMessage(token).html(...).send(chat_id, **extra)`.

## sendRichMessageDraft

Streams a partial message into a **private chat** while it's being
generated (e.g. an AI reply). Each call replaces the draft; drafts with the
same `draft_id` animate between versions. A draft is a ~30-second preview —
finish with `sendRichMessage`.

| Parameter | Meaning |
|---|---|
| `chat_id` | private chat id (integer) |
| `draft_id` | non-zero integer |
| `rich_message` | partial message; **no uploads or URL uploads** |
| `can_stop` | show a stop button; the bot gets a `stopped_message_generation` update |
| `keep_on_stop` | keep the draft when stopped |

`<tg-thinking>…</tg-thinking>` is allowed only here. Returns `true`.

Python: `await rm.send_draft(chat_id, draft_id)`.

## editMessageText

Replaces a sent message's content: pass `chat_id`, `message_id` and
`rich_message` instead of `text`. This is how interactive messages (a
calculator, a menu) update in place after a button press.

Python: `await rm.edit(chat_id, message_id)`.

## Media uploads

Media `src` can be an `http(s)` URL that Telegram downloads, or a link to an
entry of `rich_message.media`:

```json
{
  "chat_id": -1001234567890,
  "rich_message": {
    "html": "<video src=\"tg://video?id=header\"></video><p>caption text</p>",
    "media": [
      {"id": "header", "media": {"type": "animation", "media": "attach://header"}}
    ]
  }
}
```

- `id`: 1–64 chars of `A-Z a-z 0-9 _ -`, matched by the link.
- `media`: an `InputMedia*` object (`photo`, `video`, `animation`,
  `audio`, `voice_note`, `document`); only the media itself and its
  properties are used.
- `media.media`: `attach://<field>` for a new upload, a `file_id`, or a URL.
- Link kinds: `tg://photo?id=`, `tg://video?id=` (videos **and**
  animations), `tg://audio?id=` (audio and voice notes),
  `tg://document?id=`.
- **With a new upload, send the request as `multipart/form-data`**: the
  file in a form field named like the `attach://` part, and every other
  parameter as a form field, with objects (`rich_message`) JSON-encoded.
- One media entry can be referenced by several tags; each tag still counts
  toward the 50-media limit.

Python: `src = rm.attach_media("header", open("h.mp4", "rb"), "animation")`
returns `tg://video?id=header` and handles the multipart encoding.

Upload behavior found by testing is in [behavior.md](behavior.md#media).

## Ephemeral messages

A message in a shared chat that **only one user sees** (Bot API 10.2/10.3).
Typical use: a private panel opened from a public button.

Send with `ephemeral_message_parameters` on `sendRichMessage`:

| Field | Meaning |
|---|---|
| `receiver_user_id` | the only user who sees it |
| `callback_query_id` | the button press that triggered it (optional) |
| `replace_callback_query_message` | show it *in place of* the pressed message, for that user (not allowed when the press came from an ephemeral message) |

The returned `Message` has `ephemeral_message_id`. Delivery isn't
guaranteed if the user is offline.

Then:

- **Edit**: `editEphemeralMessageText` with `chat_id`, `receiver_user_id`,
  `ephemeral_message_id`, `rich_message` (Python: `rm.edit_ephemeral(...)`).
- **Delete**: `deleteEphemeralMessage` with the same three ids (Python:
  `RichMessage.delete_ephemeral(token, ...)`).
- Presses on buttons *inside* an ephemeral message arrive as normal
  callback queries whose `message` has `ephemeral_message_id` set.

The docs describe groups; testing shows it also works in **channels**, even
for users who aren't members ([behavior.md](behavior.md#ephemeral-messages)).

## Button presses (callback queries)

A `<tg-button type="callback_data" data="…">` press arrives as an update
with `callback_query`: `id`, `from` (the user), `data`, and `message` (the
message holding the button; for ephemeral messages it carries
`ephemeral_message_id`).

Read updates with `getUpdates` (long polling) or a webhook. **Only one
program may poll a bot at a time** — a second poller gets HTTP 409. Route
every interactive feature through one update loop.

Always answer each press with `answerCallbackQuery`, or the button keeps
spinning:

| Parameter | Meaning |
|---|---|
| `callback_query_id` | from the update |
| `text` | 0–200 characters; 201+ is rejected (`MESSAGE_TOO_LONG`) |
| `show_alert` | `true` = popup with OK, `false` = small toast |
| `url` | open a URL instead (only `t.me/<bot>?start=…` style links or game URLs) |
| `cache_time` | seconds the app may reuse this answer |

To update the message after a press, call `editMessageText` (or
`editEphemeralMessageText`). Batch several quick presses into one edit to
stay under rate limits.

## Errors seen in practice

| Error | Cause |
|---|---|
| `RICH_MESSAGE_EMPTY` | no visible content, e.g. `<p> </p>` (a normal space). Other invisible characters such as U+2800 are accepted |
| `RICH_MESSAGE_TABLE_COLS_TOO_MANY` | more than 20 table columns |
| `RICH_MESSAGE_BUTTONS_TOO_MANY` | more than 8 buttons in a `<tg-button-row>` |
| `RICH_MESSAGE_BUTTON_TEXT_EMPTY` | button with empty text |
| `BUTTON_DATA_INVALID` | `callback_data` over 64 bytes |
| `BUTTON_COPY_TEXT_INVALID` | `copy_text` over 256 characters |
| `RICH_MESSAGE_BLOCK_INVALID` | e.g. an inline-query button where it isn't allowed (`switch_inline_query_current_chat` in a channel) |
| `RICH_MESSAGE_MEDIA_TOO_MANY` | more than 50 media tags |
| `RICH_MESSAGE_VIDEO_INVALID` | a `.gif` uploaded with `type: "animation"` (upload it as `video`) |
| `PHOTO_INVALID_DIMENSIONS` | photo more than 20× wider than tall (or the reverse) |
| `MESSAGE_TOO_LONG` | `answerCallbackQuery` text over 200 characters |
| HTTP 429 + `retry_after` | flood limit; in a channel about 20 posts per minute. Wait `retry_after` seconds |
| HTTP 409 | another program is already polling this bot |

The server does **not** validate LaTeX: a broken formula is accepted and
shows as "invalid formula" or blank in the app.
