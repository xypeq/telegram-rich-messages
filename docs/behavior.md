# Client behavior (tested live)

Things the official docs don't say, found by sending real messages
(Oct 2026). "Phone" means the official mobile app, "desktop" means
Telegram Desktop; each was tested on one device, so other apps (iOS vs
Android, macOS, web) may differ. The API accepting a message doesn't mean
every app renders it — a lot of what's below is about that gap.

## Text and spacing

- **Line breaks:** only `<br>` (or a new block) breaks a line. Newlines in
  the HTML source become spaces.
- **Blank lines:** `<p> </p>` with a normal space is rejected
  (`RICH_MESSAGE_EMPTY`). Almost every other invisible character is
  accepted; `<p>&#x2800;</p>` (U+2800 BRAILLE PATTERN BLANK) is a reliable
  blank line. Also accepted: U+3164, U+3000, U+200B, U+FEFF and an empty
  `<p></p>`.
- Invisible characters still take up **width** (they aren't zero-width for
  layout), e.g. inside table cells.
- `<mark>` is yellow on phone and blue-ish on desktop; you can't choose.
- `<footer>` loses its small style inside table cells and quotes.
- `RM.reference` / `<a href="#id">` pointing at a `<tg-reference>` opens a
  **popup**, not a scroll. Use `<a name>` anchors to scroll.
- **File paths become command links.** Entity detection treats `/data` or
  `/mnt/photos` as bot commands (also inside table cells), so they turn
  into blue command links. Pass
  `skip_entity_detection: true` when the message shows paths.

## Tables

- At most 20 columns.
- **Links inside a table with fewer than 2 rows are not tappable.** Add a
  second row (it can hold an invisible character) when a one-row table has
  links.
- A table spans the full message width, so per-cell `align` pins content
  to the left edge, center and right edge on any screen size. That makes
  tables useful for layout, e.g. `[⇑][name][⇑]` with the arrows at the
  screen edges.
- Desktop first shrinks columns to fit, and only scrolls sideways once they
  can't shrink further. Phone never shrinks: every column is as wide as its
  content and the table scrolls sideways when it doesn't fit. Design for the
  phone behavior.
- Long cell text wraps inside its own column.
- Inline `<tg-math>` (including `\Huge`) works inside cells.
- **An emoji alone in a cell renders jumbo-sized** (like an emoji-only
  chat message), so that row becomes several times taller than the others.
  Put text next to it (`✅ ok` instead of `✅`) to keep normal row height.
  Seen on Android; desktop not checked.

## Buttons

- A `<tg-button-row>` **without `align` stretches** its buttons across the
  full width, splitting it evenly. `align="center"` (or left/right) keeps
  buttons compact.
- Long labels are truncated to fit the row; on a phone, 8 long buttons show
  only a couple of characters each. Keep phone rows short.
- Inline `<tg-button>`s inside text wrap onto the next line when the line
  is full; row buttons truncate instead.
- Inline buttons in a single centered table cell come out centered and
  compact.
- `<b>` etc. inside button text is ignored.
- `switch_inline_query_current_chat` buttons in a channel make the whole
  message fail with `RICH_MESSAGE_BLOCK_INVALID`.

## Media

- **No minimum size:** 1×1 photos and GIFs and 2×2 MP4s are accepted.
- **Photos:** at most 20:1 aspect ratio (`PHOTO_INVALID_DIMENSIONS`
  otherwise). GIFs/videos have no ratio limit.
- **Display:** apps keep the media's shape only up to **5:1**. Anything
  wider is stretched taller. So the widest banner that looks right is 5:1
  (e.g. 1280×256).
- **GIF uploads:** upload a `.gif` with media `type: "video"`. With
  `type: "animation"` it's rejected (`RICH_MESSAGE_VIDEO_INVALID`).
- **Silent MP4 as `type: "animation"`** shows like a GIF: autoplays and
  loops, and is much smaller than a GIF. Best choice for animated headers.
- **Slideshow:** up to 50 items (the per-message media limit). Phone sizes
  the frame from the **first** slide's shape; desktop from the **tallest**
  slide. Use the same shape for every slide, or put the tallest first.
- **Collage:** the layout is automatic (e.g. 3 items = 1 big + 2 small);
  you can't choose the arrangement.

## LaTeX (`<tg-math>`, `<tg-math-block>`)

Phone and desktop use different math renderers, and they disagree a lot.

Works on both:

- `\Huge` (very large). Other size commands (`\small`, `\footnotesize`…)
  weren't tested.
- Fonts and accents such as `\mathsf`, `\mathcal`, `\breve`, Greek
  capitals like `\Upsilon`.
- `\overline{…}` / `\underline{…}`. A horizontal line that works on both:
  `\overline{\phantom{xxxxxxxx}}`. A text band between two lines:
  `\overline{\underline{\phantom{xxxx}\text{text}\phantom{xxxx}}}`.
- **Stacking lines without `\\`:** `\underset{BOTTOM}{TOP}` (nest it for
  more lines), `{TOP \atop BOTTOM}`, `\genfrac{}{}{0pt}{}{TOP}{BOTTOM}`,
  `\frac`, `\mathop{X}\limits_{…}`. Add `\displaystyle` before text in
  `\underset`/`\atop` to keep it full size.
- Symbols like arrows (`\Uparrow`, `\uparrow`), `\Bigg` delimiters.

Doesn't work, or only on one app:

- **Colors never render** anywhere (`\color`, `\textcolor`, `\colorbox`).
- **`\\` line breaks** (and `array`, `matrix`, `gathered`, `substack`,
  `aligned`, `cases`…) render on desktop but are **blank on phone**. (This
  can be abused for desktop-only text.)
- `\rule` renders on phone (fixed widths like `10cm`) but **not on
  desktop**. `\linewidth`, `\hrulefill` don't work.
- `\cancel` and friends are blank on phone.
- Formula width: desktop shows **"invalid formula"** past a rendered width
  of about 116 lowercase letters (it's the drawn width that counts, not the
  source length); phone renders wide formulas but crops them at about 85
  letters, so readers have to scroll. Keep formulas narrower than a phone
  screen.
- A link containing **only** math isn't tappable; text plus math inside one
  `<a>` works. There's no `\href`.
- Text stacked under a formula *inside* the same formula (see stacking
  above) sits tight against it; a separate math block below leaves a
  visible gap.
- The server never validates LaTeX: broken formulas are accepted and fail
  in the app.

## Ephemeral messages

- Work in **channels**, although the docs describe groups.
- Work for users who aren't members of the channel (viewing it publicly).
- A public "open" button that sends the presser an ephemeral panel (with
  its own buttons, edited in place and closed with
  `deleteEphemeralMessage`) works well, e.g. a private calculator per user.
  [examples/ephemeral_panel.py](../examples/ephemeral_panel.py) is a minimal
  version with a per-user counter.

## Callback answers (`answerCallbackQuery`)

- `text` is capped at 200 characters; 201 is rejected.
- A toast (`show_alert: false`) visibly cuts off a 200-character text; a
  popup (`show_alert: true`) shows all of it.
- A tall popup (many `\n` lines within 200 chars) becomes scrollable.
- An answer with no text shows nothing (for both toasts and popups).

## Rate limits

- Posting into a channel: about 20 messages per minute before HTTP 429
  (`retry_after` ≈ 30 s).
- Batch rapid button presses into one edit per message.
