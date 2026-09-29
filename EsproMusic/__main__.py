import asyncio
import importlib

from pyrogram import filters, idle

from EsproMusic import LOGGER, app
from EsproMusic.core.call import Ritik
from EsproMusic.misc import sudo
from EsproMusic.plugins import ALL_MODULES
from EsproMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS
from player_preview import handle_player_preview_callback, send_player_preview
from rich_text_demo import send_rich_text_demo


async def init():
    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass
    await app.start()
    for all_module in ALL_MODULES:
        importlib.import_module("EsproMusic.plugins" + all_module)
    LOGGER("EsproMusic.plugins").info("Successfully Imported Modules...")
    await Ritik.start()
    await Ritik.decorators()
    LOGGER("EsproMusic").info("EsproMusicBot Started Successfully \\n\\n Yaha App ko nahi aana hai aapni hf jo bhej sakte hai @Esprosupport ")
    await idle()
    await app.stop()
    LOGGER("EsproMusic").info("Stopping Espro Music Bot...")


@app.on_message(filters.command("rich"))
async def rich_text_demo(client, message):
    await send_player_preview(client, message.chat.id)


@app.on_message(filters.command("richtext"))
async def rich_text_demo_entities(client, message):
    sender = message.from_user
    username = sender.username or sender.first_name
    await send_rich_text_demo(client, message.chat.id, username)


@app.on_callback_query(filters.regex(r"^playerpreview:"))
async def player_preview_callback(client, query):
    await handle_player_preview_callback(client, query)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
