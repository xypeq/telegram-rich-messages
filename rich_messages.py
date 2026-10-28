"""
rich_messages.py — build and send Telegram Bot API Rich Messages (Bot API 10.1-10.3).

A rich message is one HTML (or Markdown) string sent in the `rich_message`
field of sendRichMessage. Every structural element — headings, tables, maps,
collages, checklists, footnotes, formulas, buttons — is a tag inside that
string, and nesting is just nested tags.

    import asyncio
    from rich_messages import RM, RichMessage

    async def main():
        body = RM.heading("Hello", 1) + RM.paragraph("From " + RM.bold("Rich Messages"))
        await RichMessage(BOT_TOKEN).html(body).send(CHAT_ID)

    asyncio.run(main())

Three pieces:
  RM            static helpers that each return one HTML fragment. They do NOT
                escape their input, so fragments nest (RM.bold(RM.link(...))).
                Escape untrusted text yourself with RM.text(...).
  RichMessage   collects the HTML/Markdown plus uploaded files and sends,
                drafts or edits the message, including ephemeral messages.
  TelegramError raised when the Bot API answers ok=false.

The full tag reference, API methods and client behavior found by live
testing are in docs/ next to this file.

Requires: httpx (pip install httpx).
"""
import html as _html
import json
import re
from typing import List, Optional, Union

__all__ = ["RM", "RichMessage", "TelegramError"]


class RM:
    """Rich Message HTML fragments. Every method returns a str."""

    # ------------------------------------------------------------------ text
    @staticmethod
    def text(s: str) -> str:
        """Escape plain text (& < > ") so it can't be read as tags."""
        return _html.escape(s, quote=True)

    @staticmethod
    def raw(s: str) -> str:
        """Insert HTML as-is."""
        return s

    @staticmethod
    def bold(text: str) -> str: return f"<b>{text}</b>"
    @staticmethod
    def italic(text: str) -> str: return f"<i>{text}</i>"
    @staticmethod
    def underline(text: str) -> str: return f"<u>{text}</u>"
    @staticmethod
    def strike(text: str) -> str: return f"<s>{text}</s>"
    @staticmethod
    def code(text: str) -> str: return f"<code>{text}</code>"
    @staticmethod
    def sub(text: str) -> str: return f"<sub>{text}</sub>"
    @staticmethod
    def sup(text: str) -> str: return f"<sup>{text}</sup>"
    @staticmethod
    def spoiler(text: str) -> str: return f"<tg-spoiler>{text}</tg-spoiler>"

    @staticmethod
    def mark(text: str) -> str:
        """Highlighted text. The color is chosen by the app (yellow on
        mobile, blue-ish on desktop) and can't be set."""
        return f"<mark>{text}</mark>"

    # ----------------------------------------------------------------- links
    @staticmethod
    def link(text: str, url: str) -> str:
        return f'<a href="{_html.escape(url, quote=True)}">{text}</a>'

    @staticmethod
    def email(text: str, address: str) -> str:
        return RM.link(text, "mailto:" + address)

    @staticmethod
    def phone(text: str, number: str) -> str:
        return RM.link(text, "tel:" + number)

    @staticmethod
    def mention_user(text: str, user_id: int) -> str:
        return f'<a href="tg://user?id={int(user_id)}">{text}</a>'

    @staticmethod
    def anchor(name: str) -> str:
        """A jump target for RM.anchor_link(..., name)."""
        return f'<a name="{_html.escape(name, quote=True)}"></a>'

    @staticmethod
    def anchor_link(text: str, name: str) -> str:
        """A link that scrolls to RM.anchor(name) elsewhere in the message."""
        return f'<a href="#{_html.escape(name, quote=True)}">{text}</a>'

    @staticmethod
    def reference(text: str, note_id: str) -> str:
        """A footnote marker. Tapping it opens a popup showing the matching
        RM.reference_def(note_id, ...) — it does not scroll."""
        return f'<a href="#{_html.escape(note_id, quote=True)}">{text}</a>'

    @staticmethod
    def reference_def(note_id: str, text: str) -> str:
        """The popup content for RM.reference(..., note_id)."""
        return f'<tg-reference name="{_html.escape(note_id, quote=True)}">{text}</tg-reference>'

    # ---------------------------------------------------- special inline
    @staticmethod
    def custom_emoji(emoji_id: Union[int, str], placeholder: str = "") -> str:
        """Shows only if the bot owner has Telegram Premium or the bot has a
        Fragment username; otherwise `placeholder` is shown."""
        return f'<tg-emoji emoji-id="{emoji_id}">{placeholder}</tg-emoji>'

    @staticmethod
    def time(unix_ts: int, fmt: str, display_text: str) -> str:
        """A date/time shown in the reader's locale and time zone.
        fmt matches r|w?[dD]?[tT]?:
          r relative ("in 2 hours"), can't be combined
          w weekday   d short date  D long date   t short time  T long time
          ""  shows display_text unchanged."""
        if not re.fullmatch(r"r|w?[dD]?[tT]?", fmt):
            raise ValueError(f"invalid tg-time format {fmt!r}; must match r|w?[dD]?[tT]?")
        return f'<tg-time unix="{int(unix_ts)}" format="{fmt}">{display_text}</tg-time>'

    @staticmethod
    def math(latex: str) -> str:
        """Inline LaTeX. & < > in the formula are escaped for you."""
        return f"<tg-math>{_html.escape(latex, quote=False)}</tg-math>"

    # ---------------------------------------------------------------- blocks
    @staticmethod
    def heading(text: str, level: int = 1) -> str:
        if not 1 <= level <= 6:
            raise ValueError("heading level must be 1-6")
        return f"<h{level}>{text}</h{level}>"

    @staticmethod
    def paragraph(*inner: str) -> str:
        """A paragraph. Plain newlines collapse to spaces; use RM.line_break()."""
        return f"<p>{''.join(inner)}</p>"

    @staticmethod
    def line_break() -> str:
        return "<br>"

    @staticmethod
    def blank_line() -> str:
        """An empty-looking paragraph for vertical spacing. A paragraph holding
        only a normal space is rejected (RICH_MESSAGE_EMPTY), so this uses the
        invisible U+2800 BRAILLE PATTERN BLANK."""
        return "<p>⠀</p>"

    @staticmethod
    def footer(inner: str) -> str:
        """Small, dimmed text."""
        return f"<footer>{inner}</footer>"

    @staticmethod
    def divider() -> str:
        return "<hr/>"

    @staticmethod
    def pre(text: str, language: Optional[str] = None) -> str:
        """A code block. `text` is escaped for you."""
        body = _html.escape(text, quote=False)
        if language:
            return f'<pre><code class="language-{language}">{body}</code></pre>'
        return f"<pre>{body}</pre>"

    @staticmethod
    def math_block(latex: str) -> str:
        """A centered display formula. & < > are escaped for you."""
        return f"<tg-math-block>{_html.escape(latex, quote=False)}</tg-math-block>"

    @staticmethod
    def list_item(inner: str, *, checkbox: bool = False, checked: bool = False,
                  value: Optional[int] = None, item_type: Optional[str] = None) -> str:
        """checkbox=True makes a task-list item; value/item_type override the
        number or numbering style of one <ol> item."""
        if checkbox:
            return f'<li><input type="checkbox"{" checked" if checked else ""}>{inner}</li>'
        attrs = ""
        if value is not None:
            attrs += f' value="{int(value)}"'
        if item_type:
            attrs += f' type="{item_type}"'
        return f"<li{attrs}>{inner}</li>"

    @staticmethod
    def unordered_list(items: List[str]) -> str:
        return "<ul>" + "".join(items) + "</ul>"

    @staticmethod
    def ordered_list(items: List[str], *, start: Optional[int] = None,
                     list_type: Optional[str] = None, reversed_: bool = False) -> str:
        """list_type: "1", "a", "A", "i" or "I"."""
        attrs = ""
        if start is not None:
            attrs += f' start="{int(start)}"'
        if list_type:
            attrs += f' type="{list_type}"'
        if reversed_:
            attrs += " reversed"
        return f"<ol{attrs}>" + "".join(items) + "</ol>"

    @staticmethod
    def blockquote(lines: List[str], cite: Optional[str] = None, expandable: bool = False) -> str:
        """expandable=True shows a collapsed quote the reader can open."""
        body = "<br>".join(lines) + (f"<cite>{cite}</cite>" if cite else "")
        return f"<blockquote{' expandable' if expandable else ''}>{body}</blockquote>"

    @staticmethod
    def pullquote(text: str, cite: Optional[str] = None) -> str:
        """A large, emphasized quote."""
        return f"<aside>{text}{f'<cite>{cite}</cite>' if cite else ''}</aside>"

    @staticmethod
    def details(summary: str, *content: str, open_: bool = False) -> str:
        """A collapsible section; its body can hold any blocks."""
        return (f"<details{' open' if open_ else ''}><summary>{summary}</summary>"
                f"{''.join(content)}</details>")

    # ----------------------------------------------------------------- media
    @staticmethod
    def photo(src: str, *, spoiler: bool = False) -> str:
        return f'<img src="{_html.escape(src, quote=True)}"{" tg-spoiler" if spoiler else ""}/>'

    @staticmethod
    def video(src: str, *, spoiler: bool = False) -> str:
        """Videos and GIFs/animations both use <video>."""
        return f'<video src="{_html.escape(src, quote=True)}"{" tg-spoiler" if spoiler else ""}></video>'

    animation = video

    @staticmethod
    def audio(src: str) -> str:
        """An .mp3-style URL is a music track, .ogg is a voice note."""
        return f'<audio src="{_html.escape(src, quote=True)}"></audio>'

    @staticmethod
    def document(src: str) -> str:
        """A file block (Bot API 10.3)."""
        return f'<tg-document src="{_html.escape(src, quote=True)}"></tg-document>'

    @staticmethod
    def figure(media_tag: str, *, caption: Optional[str] = None, cite: Optional[str] = None) -> str:
        """Wraps one media tag or map with a caption and optional credit."""
        if caption is None and cite is None:
            return media_tag
        credit = f"<cite>{cite}</cite>" if cite else ""
        return f"<figure>{media_tag}<figcaption>{caption or ''}{credit}</figcaption></figure>"

    @staticmethod
    def map(lat: float, long: float, zoom: int = 14) -> str:
        return f'<tg-map lat="{float(lat)}" long="{float(long)}" zoom="{int(zoom)}"/>'

    @staticmethod
    def collage(media_tags: List[str], caption: Optional[str] = None) -> str:
        """A grid of photos/videos. The app picks the layout from the item
        count; you can't choose which item is big."""
        cap = f"<figcaption>{caption}</figcaption>" if caption else ""
        return "<tg-collage>" + "".join(media_tags) + cap + "</tg-collage>"

    @staticmethod
    def slideshow(media_tags: List[str], caption: Optional[str] = None) -> str:
        """One item at a time with swipe arrows. Keep every slide the same
        shape: phones size the frame from the first slide, desktop from the
        tallest one."""
        cap = f"<figcaption>{caption}</figcaption>" if caption else ""
        return "<tg-slideshow>" + "".join(media_tags) + cap + "</tg-slideshow>"

    # ---------------------------------------------------------------- tables
    @staticmethod
    def table_cell(text: str = "", *, header: bool = False, colspan: Optional[int] = None,
                   rowspan: Optional[int] = None, align: Optional[str] = None,
                   valign: Optional[str] = None) -> str:
        """Cells hold inline content only (text, links, inline math, inline
        buttons). align: left/center/right, valign: top/middle/bottom."""
        tag = "th" if header else "td"
        attrs = ""
        if colspan:
            attrs += f' colspan="{int(colspan)}"'
        if rowspan:
            attrs += f' rowspan="{int(rowspan)}"'
        if align:
            attrs += f' align="{align}"'
        if valign:
            attrs += f' valign="{valign}"'
        return f"<{tag}{attrs}>{text}</{tag}>"

    @staticmethod
    def table_row(cells: List[str]) -> str:
        return "<tr>" + "".join(cells) + "</tr>"

    @staticmethod
    def table(rows: List[str], *, bordered: bool = False, striped: bool = False,
              compact: bool = False, caption: Optional[str] = None) -> str:
        """Up to 20 columns. Links inside a table with fewer than 2 rows
        can't be tapped. compact = smaller padding (Bot API 10.3)."""
        attrs = (" bordered" if bordered else "") + (" striped" if striped else "") \
            + (" compact" if compact else "")
        cap = f"<caption>{caption}</caption>" if caption else ""
        return f"<table{attrs}>{cap}" + "".join(rows) + "</table>"

    @staticmethod
    def position(content: str, *, col: int = 1, cols: int = 3, row: int = 1, rows: int = 1,
                 align: str = "center", valign: str = "middle", compact: bool = False) -> str:
        """Places `content` in cell (row, col) of an invisible table with every
        other cell empty — a way to position inline content across the full
        message width. Note the 1-row default: links in it won't be tappable."""
        if not (1 <= row <= rows and 1 <= col <= cols):
            raise ValueError("row/col must be within rows/cols")
        if cols > 20:
            raise ValueError("a table can have at most 20 columns")
        table_rows = [
            RM.table_row([
                RM.table_cell(content, align=align, valign=valign) if (r, c) == (row, col)
                else RM.table_cell("")
                for c in range(1, cols + 1)
            ])
            for r in range(1, rows + 1)
        ]
        return RM.table(table_rows, compact=compact)

    # --------------------------------------------------------------- buttons
    BUTTON_STYLES = ("danger", "success", "primary", "link")

    @staticmethod
    def button(
        text: str,
        *,
        url: Optional[str] = None,
        callback_data: Optional[str] = None,
        web_app: Optional[str] = None,
        login_url: Optional[str] = None,
        forward_text: Optional[str] = None,
        request_write_access: bool = False,
        switch_inline_query: Optional[str] = None,
        switch_inline_query_current_chat: Optional[str] = None,
        switch_inline_query_chosen_chat: Optional[str] = None,
        allow_user_chats: bool = False,
        allow_bot_chats: bool = False,
        allow_group_chats: bool = False,
        allow_channel_chats: bool = False,
        copy_text: Optional[str] = None,
        disabled: bool = False,
        style: Optional[str] = None,
    ) -> str:
        """A <tg-button> (Bot API 10.3). Give exactly one action:
          url=               open an http(s) or tg:// link
          callback_data=     send a callback query to the bot, 1-64 bytes
          web_app=           open a Mini App (private chats only)
          login_url=         Telegram Login (domain set in @BotFather);
                             optional forward_text=, request_write_access=
          switch_inline_query=               pick a chat, insert the inline query
          switch_inline_query_current_chat=  insert the query here (not in channels)
          switch_inline_query_chosen_chat=   pick a chat of the allowed types
                                             (allow_user/bot/group/channel_chats=)
          copy_text=         copy text to the clipboard, 1-256 characters
          disabled=True      a button that does nothing
        style: danger, success, primary, or link (link: callback buttons only).
        `text` may contain RM.time(...) and RM.custom_emoji(...); other
        formatting is dropped. Use inline in a paragraph or in RM.button_row."""
        actions = {
            "url": url,
            "callback_data": callback_data,
            "web_app": web_app,
            "login_url": login_url,
            "switch_inline_query": switch_inline_query,
            "switch_inline_query_current_chat": switch_inline_query_current_chat,
            "switch_inline_query_chosen_chat": switch_inline_query_chosen_chat,
            "copy_text": copy_text,
            "disabled": True if disabled else None,
        }
        chosen = [kind for kind, value in actions.items() if value is not None]
        if len(chosen) != 1:
            raise ValueError(f"RM.button needs exactly one action, got {chosen or 'none'}")
        kind = chosen[0]
        value = actions[kind]
        if style is not None and style not in RM.BUTTON_STYLES:
            raise ValueError(f"style must be one of {RM.BUTTON_STYLES}")
        if style == "link" and kind != "callback_data":
            raise ValueError('style="link" is only allowed for callback_data buttons')
        if kind == "callback_data" and not 1 <= len(value.encode("utf-8")) <= 64:
            raise ValueError("callback_data must be 1-64 bytes")
        if kind == "copy_text" and not 1 <= len(value) <= 256:
            raise ValueError("copy_text must be 1-256 characters")
        if not text.strip():
            raise ValueError("button text can't be empty")

        def attr(name: str, raw: str) -> str:
            return f' {name}="{_html.escape(raw, quote=True)}"'

        attrs = f' type="{kind}"' + (f' style="{style}"' if style else "")
        if kind in ("url", "web_app", "login_url"):
            attrs += attr("url", value)
        elif kind == "callback_data":
            attrs += attr("data", value)
        elif kind.startswith("switch_inline_query"):
            attrs += attr("query", value)
        elif kind == "copy_text":
            attrs += attr("text", value)
        if kind == "login_url":
            if forward_text:
                attrs += attr("forward-text", forward_text)
            if request_write_access:
                attrs += " request-write-access"
        if kind == "switch_inline_query_chosen_chat":
            for flag, on in (("allow-user-chats", allow_user_chats),
                             ("allow-bot-chats", allow_bot_chats),
                             ("allow-group-chats", allow_group_chats),
                             ("allow-channel-chats", allow_channel_chats)):
                if on:
                    attrs += f" {flag}"
        return f"<tg-button{attrs}>{text}</tg-button>"

    @staticmethod
    def button_row(buttons: List[str], align: Optional[str] = None) -> str:
        """A row of 1-8 buttons. Without align the buttons stretch across the
        full width; align="center" (or left/right) keeps them compact."""
        if not 1 <= len(buttons) <= 8:
            raise ValueError("a button row holds 1-8 buttons")
        if align is not None and align not in ("left", "center", "right"):
            raise ValueError('align must be "left", "center" or "right"')
        align_attr = f' align="{align}"' if align else ""
        return f"<tg-button-row{align_attr}>" + "".join(buttons) + "</tg-button-row>"

    @staticmethod
    def thinking(text: str) -> str:
        """A "thinking…" block. Only valid in sendRichMessageDraft."""
        return f"<tg-thinking>{text}</tg-thinking>"


class TelegramError(RuntimeError):
    """A Bot API call that returned ok=false. `.description`, `.error_code`
    and `.retry_after` (seconds to wait after a 429 flood limit) come from
    Telegram's reply."""

    def __init__(self, method: str, result: dict):
        super().__init__(f"{method} failed: {result.get('description', result)}")
        self.method = method
        self.result = result
        self.error_code = result.get("error_code")
        self.description = result.get("description", "")
        self.retry_after = (result.get("parameters") or {}).get("retry_after")


class RichMessage:
    """Builds an InputRichMessage and sends it.

        rm = RichMessage(token)
        src = rm.attach_media("banner", open("banner.mp4", "rb"), "animation")
        rm.html(RM.video(src) + RM.heading("Hi", 1))
        message = await rm.send(chat_id)
    """

    API_ROOT = "https://api.telegram.org/bot{token}/{method}"

    # attach_media kind -> (InputMedia type, tg:// link kind)
    MEDIA_KINDS = {
        "photo": ("photo", "photo"),
        "video": ("video", "video"),
        "animation": ("animation", "video"),
        "audio": ("audio", "audio"),
        "voice_note": ("voice_note", "audio"),
        "document": ("document", "document"),
    }

    def __init__(self, bot_token: str):
        self._token = bot_token
        self._content: dict = {}
        self._files: dict = {}
        self._media: List[dict] = []

    def html(self, text: str, *, is_rtl: bool = False,
             skip_entity_detection: bool = False) -> "RichMessage":
        """Use Rich HTML (docs/html-reference.md). skip_entity_detection stops
        bare URLs, @mentions, #hashtags, phone numbers etc. becoming links."""
        return self._set({"html": text}, is_rtl, skip_entity_detection)

    def markdown(self, text: str, *, is_rtl: bool = False,
                 skip_entity_detection: bool = False) -> "RichMessage":
        """Use Rich Markdown (GitHub-flavored, may contain the same HTML tags)."""
        return self._set({"markdown": text}, is_rtl, skip_entity_detection)

    def _set(self, content: dict, is_rtl: bool, skip_entity_detection: bool) -> "RichMessage":
        self._content = content
        if is_rtl:
            content["is_rtl"] = True
        if skip_entity_detection:
            content["skip_entity_detection"] = True
        return self

    def attach_media(self, name: str, file, kind: str = "photo") -> str:
        """Registers media for this message and returns the tg:// link to use
        as `src`, e.g. RM.photo(rm.attach_media("chart", open("c.png", "rb"))).

        file: an open binary file (uploaded with the message), or a string —
              a file_id already on Telegram or an http(s) URL.
        kind: photo, video, animation, audio, voice_note or document.
              Upload a .gif as "video" ("animation" rejects GIFs with
              RICH_MESSAGE_VIDEO_INVALID); a silent .mp4 as "animation" shows
              as an autoplaying, looping GIF.
        name: 1-64 characters of A-Z a-z 0-9 _ -, unique within the message.
        One upload can be referenced several times; each reference still
        counts toward the 50-media limit."""
        if kind not in self.MEDIA_KINDS:
            raise ValueError(f"kind must be one of {list(self.MEDIA_KINDS)}")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", name):
            raise ValueError("name must be 1-64 characters of A-Z, a-z, 0-9, _ and -")
        if any(entry["id"] == name for entry in self._media):
            raise ValueError(f"media name {name!r} is already used in this message")
        media_type, link_kind = self.MEDIA_KINDS[kind]
        if isinstance(file, str):
            source = file
        else:
            self._files[name] = file
            source = f"attach://{name}"
        self._media.append({"id": name, "media": {"type": media_type, "media": source}})
        return f"tg://{link_kind}?id={name}"

    def payload(self) -> dict:
        """The InputRichMessage object as a dict."""
        if not self._content:
            raise ValueError("call .html(...) or .markdown(...) first")
        payload = dict(self._content)
        if self._media:
            payload["media"] = list(self._media)
        return payload

    async def send(self, chat_id, *, reply_to_message_id: Optional[int] = None,
                   ephemeral_to: Optional[int] = None, callback_query_id: Optional[str] = None,
                   replace_callback_message: bool = False, **extra_params) -> dict:
        """sendRichMessage. Returns the sent Message.

        ephemeral_to=user_id sends an ephemeral message only that user sees
        (the result then carries `ephemeral_message_id`). Pass the
        callback_query_id when it answers a button press, and
        replace_callback_message=True to show it in place of the pressed
        message. Any other sendRichMessage parameter can go in extra_params."""
        params = {"chat_id": chat_id, "rich_message": self.payload(), **extra_params}
        if reply_to_message_id is not None:
            params.setdefault("reply_parameters", {"message_id": reply_to_message_id})
        if ephemeral_to is not None:
            ephemeral = {"receiver_user_id": ephemeral_to}
            if callback_query_id:
                ephemeral["callback_query_id"] = callback_query_id
            if replace_callback_message:
                ephemeral["replace_callback_query_message"] = True
            params["ephemeral_message_parameters"] = ephemeral
        return await self._post("sendRichMessage", params)

    async def send_draft(self, chat_id: int, draft_id: int, **extra_params) -> bool:
        """sendRichMessageDraft: stream a partial message into a private chat.
        Drafts last ~30 s; send the final version with send(). Uploads aren't
        allowed in drafts."""
        return await self._post("sendRichMessageDraft", {
            "chat_id": chat_id, "draft_id": draft_id, "rich_message": self.payload(), **extra_params})

    async def edit(self, chat_id, message_id: int, **extra_params) -> dict:
        """editMessageText: replace an existing message with this rich message."""
        return await self._post("editMessageText", {
            "chat_id": chat_id, "message_id": message_id, "rich_message": self.payload(), **extra_params})

    async def edit_ephemeral(self, chat_id, receiver_user_id: int, ephemeral_message_id: int,
                             **extra_params) -> bool:
        """editEphemeralMessageText: replace an ephemeral message's content."""
        return await self._post("editEphemeralMessageText", {
            "chat_id": chat_id, "receiver_user_id": receiver_user_id,
            "ephemeral_message_id": ephemeral_message_id, "rich_message": self.payload(),
            **extra_params})

    @classmethod
    async def delete_ephemeral(cls, bot_token: str, chat_id, receiver_user_id: int,
                               ephemeral_message_id: int) -> bool:
        """deleteEphemeralMessage."""
        return await cls(bot_token)._post("deleteEphemeralMessage", {
            "chat_id": chat_id, "receiver_user_id": receiver_user_id,
            "ephemeral_message_id": ephemeral_message_id})

    async def _post(self, method: str, data: dict):
        import httpx
        url = self.API_ROOT.format(token=self._token, method=method)
        async with httpx.AsyncClient(timeout=60) as client:
            if self._files:
                # Uploads go as multipart/form-data with JSON-encoded objects.
                form = {k: v if isinstance(v, str) else json.dumps(v) for k, v in data.items()}
                resp = await client.post(url, data=form, files=self._files)
            else:
                resp = await client.post(url, json=data)
        result = resp.json()
        if not result.get("ok"):
            raise TelegramError(method, result)
        return result["result"]
