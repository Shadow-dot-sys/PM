from pyrogram.enums import ButtonStyle
from pyrogram.types import (
    DisabledButton,
    InputRichBlockButtons,
    InputRichBlockParagraph,
    InputRichMessage,
    RichMessageButton,
)


_PREVIEWS = {}
_DURATION = 266


def _format_time(seconds):
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


def _progress_bar(elapsed):
    bars = 12
    filled = min(int(elapsed / _DURATION * bars), bars)
    if filled == 0:
        return "⚪" + "─" * (bars - 1)
    if filled == bars:
        return "─" * (bars - 1) + "⚪"
    return "─" * (filled - 1) + "⚪" + "─" * (bars - filled)


def _caption(state):
    status = "⏸ Music Is Paused" if state["paused"] else "🎧 Music Is Playing"
    return (
        f"{status}\n\n"
        f"🎵 Now Playing: {state['title']}\n"
        f"⏱ Track Duration: {_format_time(_DURATION)}\n"
        "👤 Requested By: Autoplay\n\n"
        "🎶 Your track is now playing\n"
        "🔊 Sit back, relax & enjoy the music"
    )


def _blocks(state):
    elapsed = _format_time(state["elapsed"])
    duration = _format_time(_DURATION)
    play_label = "▶ Play" if state["paused"] else "Ⅱ Pause"
    return [
        InputRichBlockParagraph(text=_caption(state)),
        InputRichBlockButtons(
            buttons=[
                RichMessageButton(
                    text=f"{elapsed}  {_progress_bar(state['elapsed'])}  {duration}",
                    disabled=DisabledButton(),
                )
            ],
            align="center",
        ),
        InputRichBlockButtons(
            buttons=[
                RichMessageButton(
                    text="↺ Replay",
                    style=ButtonStyle.DANGER,
                    callback_data="playerpreview:replay",
                ),
                RichMessageButton(
                    text=play_label,
                    callback_data="playerpreview:pause",
                ),
                RichMessageButton(
                    text="» Skip",
                    style=ButtonStyle.PRIMARY,
                    callback_data="playerpreview:skip",
                ),
            ],
            align="center",
        ),
        InputRichBlockButtons(
            buttons=[
                RichMessageButton(
                    text="☰ Queue · 0",
                    style=ButtonStyle.SUCCESS,
                    callback_data="playerpreview:queue",
                )
            ],
            align="center",
        ),
    ]


async def _send_player_preview(client, chat_id, state):
    message = await client.send_rich_message(
        chat_id=chat_id,
        rich_message=InputRichMessage(blocks=_blocks(state)),
    )
    _PREVIEWS[(message.chat.id, message.id)] = state.copy()
    return message


async def send_player_preview(client, chat_id):
    await _send_player_preview(
        client,
        chat_id,
        {
            "title": "Sitaare [Slowed+Reverb]",
            "elapsed": 74,
            "paused": False,
        },
    )


async def handle_player_preview_callback(client, query):
    if not query.message:
        return await query.answer()

    key = (query.message.chat.id, query.message.id)
    state = _PREVIEWS.get(key)
    if not state:
        return await query.answer("Send /rich to create a new preview.", show_alert=True)

    action = query.data.partition(":")[2]
    if action == "queue":
        return await query.answer("The demo queue is empty.", show_alert=True)
    if action == "progress":
        return await query.answer()
    if action == "pause":
        state["paused"] = not state["paused"]
        answer = "Playback paused." if state["paused"] else "Playback resumed."
    elif action == "replay":
        state["elapsed"] = 0
        answer = "Restarted the demo track."
    elif action == "skip":
        state["title"] = "Another Demo Track"
        state["elapsed"] = 0
        answer = "Skipped to the next demo track."
    else:
        return await query.answer()

    await query.answer(answer)
    await _send_player_preview(client, key[0], state)
    _PREVIEWS.pop(key, None)
    await client.delete_messages(chat_id=key[0], message_ids=key[1])