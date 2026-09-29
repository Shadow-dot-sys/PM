import asyncio

from pyrogram.types import (
    InputRichBlockParagraph,
    InputRichMessage,
    RichText,
    RichTextBold,
    RichTextCode,
    RichTextCustomEmoji,
    RichTextEmailAddress,
    RichTextHashtag,
    RichTextItalic,
    RichTextMention,
    RichTextStrikethrough,
    RichTextSubscript,
    RichTextSuperscript,
    RichTextUnderline,
    RichTextUrl,
)


async def send_rich_text_demo(client, chat_id, username):
    samples: list[tuple[str, RichText]] = [
        ("Bold", RichTextBold("Important")),
        ("Italic", RichTextItalic("Emphasized")),
        ("Underline", RichTextUnderline("Underlined")),
        ("Strikethrough", RichTextStrikethrough("Deleted")),
        ("Code", RichTextCode("print('hello')")),
        ("Subscript", RichTextSubscript("H2O")),
        ("Superscript", RichTextSuperscript("E=mc2")),
        ("Mention", RichTextMention(f"@{username}", username)),
        ("Hashtag", RichTextHashtag("#python", "python")),
        ("URL", RichTextUrl("Click Here", url="https://example.com")),
        (
            "Email",
            RichTextEmailAddress("contact@example.com", "contact@example.com"),
        ),
        ("Custom emoji", RichTextCustomEmoji("5471952286193600537", "😀")),
    ]

    combined: list[str | RichText] = []
    for _, sample in samples:
        if combined:
            combined.append(" | ")
        combined.append(sample)

    try:
        await client.send_rich_message(
            chat_id=chat_id,
            rich_message=InputRichMessage(
                blocks=[InputRichBlockParagraph(text=combined)]
            ),
        )
        return
    except Exception as error:
        if "RICH_MESSAGE_RICH_TEXT_INVALID" not in str(error):
            raise

    rejected = []
    for label, sample in samples:
        try:
            await client.send_rich_message(
                chat_id=chat_id,
                rich_message=InputRichMessage(
                    blocks=[InputRichBlockParagraph(text=[sample])]
                ),
            )
        except Exception as error:
            rejected.append(f"{label} ({type(error).__name__})")
        await asyncio.sleep(1)

    if rejected:
        await client.send_message(
            chat_id=chat_id,
            text="Telegram rejected these RichText types: " + ", ".join(rejected),
        )