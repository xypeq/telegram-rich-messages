"""
A public "open panel" button. Pressing it sends the presser a private
(ephemeral) panel only they can see: a personal counter with its own
buttons, edited in place, plus a Close button that deletes it.

Shows the full interactive loop: callback buttons, answerCallbackQuery,
ephemeral send / edit / delete, and long polling with getUpdates.

    export BOT_TOKEN=123:abc CHAT_ID=-1001234567890
    python examples/ephemeral_panel.py

Only one program may poll a bot at a time (a second one gets HTTP 409).
State is kept in memory, so a restart resets the counters.
"""
import asyncio
import html
import os
import sys

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rich_messages import RM, RichMessage, TelegramError  # noqa: E402

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
API = f"https://api.telegram.org/bot{BOT_TOKEN}/"
PREFIX = "panel:"

counters = {}   # (chat_id, user_id) -> int
open_panels = {}  # (chat_id, user_id) -> ephemeral_message_id


def public_button() -> str:
    return RM.button_row([RM.button("open panel", callback_data=PREFIX + "open", style="primary")],
                         align="center")


def panel(user: dict, count: int) -> str:
    name = html.escape(user.get("first_name") or "you")
    return "".join([
        RM.heading(f"Only {name} sees this", 3),
        RM.math_block(rf"\Huge {count}"),
        RM.button_row([
            RM.button("−1", callback_data=PREFIX + "dec"),
            RM.button("+1", callback_data=PREFIX + "inc", style="success"),
        ], align="center"),
        RM.button_row([RM.button("Close", callback_data=PREFIX + "close", style="danger")],
                      align="center"),
    ])


async def answer(http: httpx.AsyncClient, query_id: str, text: str = None) -> None:
    body = {"callback_query_id": query_id}
    if text:
        body["text"] = text[:200]
    await http.post(API + "answerCallbackQuery", json=body)


async def handle(http: httpx.AsyncClient, query: dict) -> None:
    action = query["data"][len(PREFIX):]
    user = query["from"]
    chat_id = query["message"]["chat"]["id"]
    key = (chat_id, user["id"])
    try:
        if action == "open":
            if key in open_panels:  # keep one panel per user
                await RichMessage.delete_ephemeral(BOT_TOKEN, chat_id, user["id"], open_panels.pop(key))
            sent = await RichMessage(BOT_TOKEN).html(panel(user, counters.get(key, 0))).send(
                chat_id, ephemeral_to=user["id"], callback_query_id=query["id"])
            open_panels[key] = sent["ephemeral_message_id"]
        elif action in ("inc", "dec"):
            counters[key] = counters.get(key, 0) + (1 if action == "inc" else -1)
            await RichMessage(BOT_TOKEN).html(panel(user, counters[key])).edit_ephemeral(
                chat_id, user["id"], query["message"]["ephemeral_message_id"])
        elif action == "close":
            await RichMessage.delete_ephemeral(
                BOT_TOKEN, chat_id, user["id"], query["message"]["ephemeral_message_id"])
            open_panels.pop(key, None)
        await answer(http, query["id"])
    except TelegramError as error:
        await answer(http, query["id"], f"Error: {error.description}")


async def main() -> None:
    message = await RichMessage(BOT_TOKEN).html(public_button()).send(CHAT_ID)
    print("posted the button, message id", message["message_id"])
    offset = None
    async with httpx.AsyncClient(timeout=45) as http:
        while True:
            reply = (await http.post(API + "getUpdates", json={"offset": offset, "timeout": 30})).json()
            if not reply.get("ok"):
                sys.exit(f"getUpdates failed: {reply.get('description')}")
            for update in reply["result"]:
                offset = update["update_id"] + 1
                query = update.get("callback_query")
                if query and query.get("data", "").startswith(PREFIX):
                    await handle(http, query)


asyncio.run(main())
