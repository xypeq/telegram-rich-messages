# Rich HTML reference

Every tag a rich message understands (Bot API 10.1–10.3), with attributes,
plus the Python helper that produces it. Send the HTML as
`rich_message.html` in `sendRichMessage`. Markdown is summarized at the end.

Tags not listed here are not supported. Nesting is allowed up to 16 levels.

## Escaping

- Escape `&`, `<`, `>` in text (and `"` in attribute values). Supported
  named entities: `&lt; &gt; &amp; &quot; &apos; &nbsp; &hellip; &mdash;
  &ndash; &lsquo; &rsquo; &ldquo; &rdquo;`. All numeric entities (`&#8212;`)
  work.
- **Newlines in the source don't break lines.** Like normal HTML they
  collapse to a space. Use `<br>` or separate `<p>` blocks.
- LaTeX goes inside `<tg-math>` / `<tg-math-block>` as raw LaTeX, but `&`,
  `<`, `>` in it still need HTML escaping.

## Inline formatting

| HTML | Result | Helper |
|---|---|---|
| `<b>`, `<strong>` | bold | `RM.bold` |
| `<i>`, `<em>` | italic | `RM.italic` |
| `<u>`, `<ins>` | underline | `RM.underline` |
| `<s>`, `<strike>`, `<del>` | strikethrough | `RM.strike` |
| `<code>` | inline monospace (no language) | `RM.code` |
| `<mark>` | highlighted; color picked by the app | `RM.mark` |
| `<sub>`, `<sup>` | subscript, superscript | `RM.sub`, `RM.sup` |
| `<tg-spoiler>` | hidden until tapped | `RM.spoiler` |
| `<tg-math>x^2</tg-math>` | inline LaTeX | `RM.math` |
| `<tg-time unix="1647531900" format="wDT">fallback</tg-time>` | date/time in the reader's locale | `RM.time` |
| `<tg-emoji emoji-id="…">fallback</tg-emoji>` | custom emoji (needs bot owner Premium or Fragment username) | `RM.custom_emoji` |
| `<img src="tg://emoji?id=…" alt=""/>` | custom emoji, alternative form | — |

`tg-time` `format` matches `r|w?[dD]?[tT]?`: `r` relative (alone only), `w`
weekday, `d` short date, `D` long date, `t` short time, `T` long time, empty
= show the text as written.

## Links

| HTML | Result | Helper |
|---|---|---|
| `<a href="https://…">` | link (the app asks before opening) | `RM.link` |
| `<a href="mailto:…">` | e-mail link | `RM.email` |
| `<a href="tel:+1…">` | phone link | `RM.phone` |
| `<a href="tg://user?id=123">` | mention by user id | `RM.mention_user` |
| `<a name="intro"></a>` | anchor (jump target) | `RM.anchor` |
| `<a href="#intro">` | scroll to that anchor | `RM.anchor_link` |
| `<tg-reference name="n1">text</tg-reference>` | footnote content | `RM.reference_def` |
| `<a href="#n1">¹</a>` | opens the footnote as a **popup** | `RM.reference` |

Bare URLs, e-mails, `@usernames`, `#hashtags`, `$CASHTAGS`, `/commands`,
phone and card numbers become links automatically unless
`skip_entity_detection: true`.

## Blocks

| HTML | Result | Helper |
|---|---|---|
| `<h1>`…`<h6>` | headings | `RM.heading(text, level)` |
| `<p>` | paragraph | `RM.paragraph` |
| `<br>` | line break inside a block | `RM.line_break` |
| `<footer>` | small dimmed text | `RM.footer` |
| `<hr/>` | divider | `RM.divider` |
| `<pre>…</pre>` | code block | `RM.pre(text)` |
| `<pre><code class="language-python">…</code></pre>` | code block with language | `RM.pre(text, "python")` |
| `<tg-math-block>E = mc^2</tg-math-block>` | centered display formula | `RM.math_block` |
| `<ul><li>` / `<ol><li>` | lists | `RM.unordered_list`, `RM.ordered_list`, `RM.list_item` |
| `<ol start="3" type="a" reversed>` | numbering start, style (`1 a A i I`), reversed | `RM.ordered_list(start=, list_type=, reversed_=)` |
| `<li value="7" type="i">` | number/style of one item | `RM.list_item(value=, item_type=)` |
| `<li><input type="checkbox" checked>…</li>` | task list item | `RM.list_item(checkbox=True, checked=)` |
| `<blockquote>…<cite>Author</cite></blockquote>` | quote with credit | `RM.blockquote(lines, cite=)` |
| `<blockquote expandable>` | collapsed quote that expands | `RM.blockquote(..., expandable=True)` |
| `<aside>…<cite>Author</cite></aside>` | large pull quote | `RM.pullquote` |
| `<details open><summary>Title</summary>…</details>` | collapsible section; body takes any blocks; `open` = expanded at first | `RM.details(summary, *blocks, open_=)` |

## Media

| HTML | Result | Helper |
|---|---|---|
| `<img src="…"/>` | photo | `RM.photo` |
| `<video src="…"></video>` | video, or GIF/animation | `RM.video` |
| `<audio src="….mp3"></audio>` | music track (`.ogg` = voice note) | `RM.audio` |
| `<tg-document src="…"></tg-document>` | file (10.3) | `RM.document` |
| `tg-spoiler` attribute on `img`/`video` | blurred until tapped | `spoiler=True` |
| `<figure>MEDIA<figcaption>Caption<cite>Credit</cite></figcaption></figure>` | caption + credit; also works around `<tg-map>` and `<tg-document>` | `RM.figure` |
| `<tg-map lat="41.9" long="12.5" zoom="14"/>` | interactive map | `RM.map` |
| `<tg-collage>MEDIA…<figcaption>…</figcaption></tg-collage>` | auto-layout grid | `RM.collage` |
| `<tg-slideshow>MEDIA…<figcaption>…</figcaption></tg-slideshow>` | swipeable, one at a time | `RM.slideshow` |

Media are blocks of their own (not inside a paragraph). `src` is an
`http(s)` URL, or `tg://photo?id=X`, `tg://video?id=X`, `tg://audio?id=X`,
`tg://document?id=X` pointing at entry `X` of `rich_message.media` (uploads
and file_ids, see [api.md](api.md#media-uploads)). The media type comes from
the MIME type and URL.

## Tables

```html
<table bordered striped compact>
  <caption>Caption</caption>
  <tr><th>Header</th><th>Header</th></tr>
  <tr><td colspan="2" rowspan="1" align="center" valign="middle">Value</td></tr>
</table>
```

- Table flags: `bordered`, `striped`, `compact` (10.3, smaller padding).
- Cell attributes: `colspan`, `rowspan`, `align` (`left|center|right`),
  `valign` (`top|middle|bottom`).
- Cells take **inline content only**: formatting, links, `<tg-math>`,
  inline `<tg-button>`s. No blocks.
- At most **20 columns**.
- Helpers: `RM.table`, `RM.table_row`, `RM.table_cell`, and `RM.position`
  (content in one cell of an invisible grid).

## Buttons (Bot API 10.3)

Buttons live *inside* the message, unlike classic inline keyboards.

```html
<tg-button-row align="center">
  <tg-button type="url" style="primary" url="https://example.com">Site</tg-button>
  <tg-button type="callback_data" data="vote:1">Vote</tg-button>
</tg-button-row>
<p>Inline: <tg-button type="copy_text" text="hello">Copy</tg-button></p>
```

| `type` | Attributes | Notes |
|---|---|---|
| `url` | `url` | http(s) or `tg://` link; `tg://user?id=` mentions |
| `callback_data` | `data` (1–64 bytes) | sends a callback query to the bot |
| `web_app` | `url` | Mini App; private chats only |
| `login_url` | `url`, `forward-text`, `request-write-access` | domain set in @BotFather; not in ephemeral messages |
| `switch_inline_query` | `query` | pick a chat, insert `@bot query` |
| `switch_inline_query_current_chat` | `query` | insert in this chat; **not in channels** |
| `switch_inline_query_chosen_chat` | `query`, `allow-user-chats`, `allow-bot-chats`, `allow-group-chats`, `allow-channel-chats` | pick a chat of those types |
| `copy_text` | `text` (1–256 chars) | copies to clipboard |
| `disabled` | — | does nothing |

- `style`: `danger`, `success`, `primary`, or `link` (`link` = borderless,
  callback buttons only).
- Button text may contain only plain text, `<tg-time>` and `<tg-emoji>`.
- `<tg-button-row>` holds 1–8 buttons; `align` = `left|center|right`.
- Inline `<tg-button>` can sit in paragraphs, list items, quotes, table
  cells and so on.
- Helpers: `RM.button(text, url=… | callback_data=… | …, style=)`,
  `RM.button_row(buttons, align=)`.

## Drafts only

`<tg-thinking>Thinking…</tg-thinking>` (`RM.thinking`) is allowed only in
`sendRichMessageDraft`.

## Limits

| Limit | Value |
|---|---|
| Text length | 32768 UTF-8 characters, including formula source and custom emoji alt text |
| Blocks | 500, counting nested blocks, list items, table rows, quotes, details |
| Nesting | 16 levels |
| Media | 50 in total (each tag counts, even if it reuses one upload) |
| Table columns | 20 |
| Buttons per row | 8 |

## Rich Markdown

Pass `rich_message.markdown` instead of `html`. It's GitHub-flavored
Markdown and may contain the HTML tags above.

~~~markdown
**bold** __bold__ *italic* _italic_ ~~strike~~ `code` ==marked== ||spoiler||
[link](https://t.me/)  $x^2$  ![](tg://emoji?id=5368324170671202286)
![22:45 tomorrow](tg://time?unix=1647531900&format=wDT)

# Heading 1 … ###### Heading 6
```python
code
```
---
- item    1. item    - [ ] task    - [x] done
>quote
![](https://telegram.org/example/photo.jpg "Caption")
| Header | Header |
|:-------|:------:|
| left   | center |
Footnote[^id1]
[^id1]: Footnote text.
$$E = mc^2$$
~~~

- Media must be on its own line as a block.
- Markdown isn't parsed inside block HTML tags, except inside `<details>`,
  `<tg-collage>` and `<tg-slideshow>` (leave blank lines around the content).
- Features without Markdown syntax (underline, sub/sup, anchors, pull
  quotes, maps, buttons) use the HTML tags.

## The `blocks` alternative

Instead of `html`/`markdown`, `rich_message.blocks` can be an array of
`InputRichBlock*` JSON objects (paragraphs, headings, tables, …). This
library and these docs use HTML, which covers the same features. See the
official [Bot API docs](https://core.telegram.org/bots/api#inputrichmessage)
for the block objects.
