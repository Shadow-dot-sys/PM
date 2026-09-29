import asyncio
import os

from dotenv import load_dotenv
from pyrogram import Client, filters, idle

from player_preview import handle_player_preview_callback, send_player_preview
from rich_text_demo import send_rich_text_demo


def load_settings():
    load_dotenv()
    required = ("API_ID", "API_HASH", "BOT_TOKEN")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        names = ", ".join(missing)
        raise SystemExit(
            f"Missing {names}. Set these in your local .env file before starting."
        )

    try:
        api_id = int(os.environ["API_ID"])
    except ValueError as error:
        raise SystemExit("API_ID must be an integer.") from error

    return api_id, os.environ["API_HASH"], os.environ["BOT_TOKEN"]


async def run_demo(api_id, api_hash, bot_token):
    client = Client(
        "rich_text_demo",
        api_id=api_id,
        api_hash=api_hash,
        bot_token=bot_token,
        in_memory=True,
    )

    @client.on_message(filters.command("rich"))
    async def player_preview(bot, message):
        await send_player_preview(bot, message.chat.id)

    @client.on_message(filters.command("richtext"))
    async def rich_text_demo(bot, message):
        username = bot.me.username or "username"
        await send_rich_text_demo(bot, message.chat.id, username)

    @client.on_callback_query(filters.regex(r"^playerpreview:"))
    async def player_preview_callback(bot, query):
        await handle_player_preview_callback(bot, query)

    await client.start()
    print(f"RichText demo is running as @{client.me.username}. Send /rich to test.")
    try:
        await idle()
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(run_demo(*load_settings()))