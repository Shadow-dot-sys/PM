from pyrogram.types import InlineKeyboardButton

from EsproMusic import app
from EsproMusic.misc import db
from EsproMusic.utils.formatters import (
    seekbar,
    played_percentage,
    time_to_seconds,
)


def _autoplay_label(chat_id) -> str:
    try:
        from EsproMusic.plugins.tools.autoplay import autoplay_label

        label = autoplay_label(chat_id)

        if "OFF" in label:
            return "🔄 AutoPlay: OFF"

        return "🔄 AutoPlay: ON"

    except Exception:
        return "🔄 AutoPlay: OFF"


def track_markup(_, videoid, user_id, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=(
                    f"MusicStream {videoid}|{user_id}|a|{channel}|{fplay}"
                ),
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=(
                    f"MusicStream {videoid}|{user_id}|v|{channel}|{fplay}"
                ),
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]

    return buttons


def stream_markup(_, chat_id, videoid="", played=0, dur_sec=0, is_playing=True):
    buttons = []

    # =========================================================
    # PROGRESS BAR: {progress} ───⚪─────── {total}
    # =========================================================

    if dur_sec and dur_sec > 0:
        percent = played_percentage(played, dur_sec)
        
        played_str = seconds_to_min_local(played)
        dur_str = seconds_to_min_local(dur_sec)

        # Progress bar with circle indicator
        bar = _get_progress_bar(percent)
        
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{played_str} {bar} {dur_str}",
                    callback_data="noop",
                )
            ]
        )

    # =========================================================
    # MAIN CONTROL: Only Play/Pause (No Replay, No Skip)
    # =========================================================

    control_text = "⏸ Pause" if is_playing else "▶️ Play"
    control_callback = f"ADMIN {'Pause' if is_playing else 'Resume'}|{chat_id}"

    buttons.append(
        [
            InlineKeyboardButton(
                text=control_text,
                callback_data=control_callback,
            )
        ]
    )

    # =========================================================
    # QUEUE DISPLAY
    # =========================================================

    try:
        queue = db.get(chat_id, [])
        queue_count = max(len(queue) - 1, 0)
    except Exception:
        queue_count = 0

    buttons.append(
        [
            InlineKeyboardButton(
                text=f"☰ Queue • {queue_count}",
                callback_data="noop",
            )
        ]
    )

    # =========================================================
    # EXTRA: AutoPlay + Add Song
    # =========================================================

    buttons.append(
        [
            InlineKeyboardButton(
                text=_autoplay_label(chat_id),
                callback_data=f"ADMIN AutoPlay|{chat_id}",
            ),
            InlineKeyboardButton(
                text="➕ Add Song",
                url=(
                    f"https://t.me/{app.username}?start=addpl_{videoid}"
                    if videoid
                    else f"https://t.me/{app.username}?start=my_playlists"
                ),
            ),
        ]
    )

    # =========================================================
    # CLOSE BUTTON
    # =========================================================

    buttons.append(
        [
            InlineKeyboardButton(
                text="✖ Close",
                callback_data=f"ADMIN Close|{chat_id}",
            )
        ]
    )

    return buttons


def _get_progress_bar(percent: int) -> str:
    """Generate progress bar with circle indicator"""
    total_bars = 12
    
    filled = int((percent / 100) * total_bars)
    empty = total_bars - filled
    
    # Circle position based on percentage
    if filled == 0:
        return "⚪" + "─" * (total_bars - 1)
    elif filled >= total_bars:
        return "─" * (total_bars - 1) + "⚪"
    else:
        return "─" * (filled - 1) + "⚪" + "─" * empty


def seconds_to_min_local(seconds):
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)

    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"

    return f"{m:02d}:{s:02d}"


def stream_markup_timer(_, chat_id, played, dur, videoid="", is_playing=True):
    try:
        played_sec = time_to_seconds(played)
        dur_sec = time_to_seconds(dur)

    except Exception:
        played_sec, dur_sec = 0, 0

    return stream_markup(
        _,
        chat_id,
        videoid,
        played_sec,
        dur_sec,
        is_playing,
    )


def playlist_markup(_, videoid, user_id, ptype, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=(
                    f"RitikPlaylists "
                    f"{videoid}|{user_id}|{ptype}|a|{channel}|{fplay}"
                ),
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=(
                    f"RitikPlaylists "
                    f"{videoid}|{user_id}|{ptype}|v|{channel}|{fplay}"
                ),
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]

    return buttons


def livestream_markup(_, videoid, user_id, mode, channel, fplay):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_3"],
                callback_data=(
                    f"LiveStream "
                    f"{videoid}|{user_id}|{mode}|{channel}|{fplay}"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {videoid}|{user_id}",
            )
        ],
    ]

    return buttons


def slider_markup(_, videoid, user_id, query, query_type, channel, fplay):
    query = f"{query[:20]}"

    buttons = [
        [
            InlineKeyboardButton(
                text=_["P_B_1"],
                callback_data=(
                    f"MusicStream "
                    f"{videoid}|{user_id}|a|{channel}|{fplay}"
                ),
            ),
            InlineKeyboardButton(
                text=_["P_B_2"],
                callback_data=(
                    f"MusicStream "
                    f"{videoid}|{user_id}|v|{channel}|{fplay}"
                ),
            ),
        ],
        [
            InlineKeyboardButton(
                text="◁",
                callback_data=(
                    f"slider B|{query_type}|{query}|{user_id}|{channel}|{fplay}"
                ),
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"],
                callback_data=f"forceclose {query}|{user_id}",
            ),
            InlineKeyboardButton(
                text="▷",
                callback_data=(
                    f"slider F|{query_type}|{query}|{user_id}|{channel}|{fplay}"
                ),
            ),
        ],
    ]

    return buttons
