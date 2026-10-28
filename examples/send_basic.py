"""
Sends one rich message that shows most building blocks: heading, formatted
text, a table, a formula, a collapsible section, an uploaded image and a
row of buttons.

    export BOT_TOKEN=123:abc CHAT_ID=-1001234567890
    python examples/send_basic.py [optional/path/to/image.png]
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rich_messages import RM, RichMessage, TelegramError  # noqa: E402

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]


async def main() -> None:
    rm = RichMessage(BOT_TOKEN)
    image = rm.attach_media("image", open(sys.argv[1], "rb")) if len(sys.argv) > 1 \
        else "https://telegram.org/example/photo.jpg"

    body = "".join([
        RM.heading("Weekly report", 1),
        RM.paragraph("Shipped " + RM.bold("3 features") + ", fixed "
                     + RM.spoiler("too many") + " bugs. "
                     + RM.link("Changelog", "https://example.com/changelog")),
        RM.table([
            RM.table_row([RM.table_cell("Metric", header=True),
                          RM.table_cell("Value", header=True, align="right")]),
            RM.table_row([RM.table_cell("Users"), RM.table_cell("1,204", align="right")]),
            RM.table_row([RM.table_cell("Uptime"), RM.table_cell("99.98%", align="right")]),
        ], bordered=True, compact=True),
        RM.math_block(r"\text{growth} = \frac{1204 - 980}{980} \approx 22.9\%"),
        RM.details("Details", RM.unordered_list([
            RM.list_item("Faster search", checkbox=True, checked=True),
            RM.list_item("Dark mode", checkbox=True),
        ])),
        RM.figure(RM.photo(image), caption="This week's screenshot"),
        RM.button_row([
            RM.button("Open dashboard", url="https://example.com", style="primary"),
            RM.button("Copy summary", copy_text="3 features, 1204 users"),
        ], align="center"),
        RM.footer("Sent with rich_messages.py"),
    ])
    try:
        message = await rm.html(body).send(CHAT_ID)
        print("sent, message id", message["message_id"])
    except TelegramError as error:
        print("Telegram rejected it:", error.description)


asyncio.run(main())
