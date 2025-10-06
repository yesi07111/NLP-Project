from telethon.tl.types import (
    PeerUser,
    PeerChat,
    PeerChannel,
    MessageEntityMention,
    MessageEntityMentionName,
)
from utils.text_processing import clean_message_text


async def parse_message(msg):
    """Extrae información estructurada de un objeto Message de Telethon"""
    sender_id = None
    sender_name = None
    sender_username = None

    if isinstance(msg.from_id, PeerUser):
        sender_id = msg.from_id.user_id
    elif isinstance(msg.from_id, PeerChat):
        sender_id = msg.from_id.chat_id
    elif isinstance(msg.from_id, PeerChannel):
        sender_id = msg.from_id.channel_id

    if hasattr(msg, "sender"):
        sender = msg.sender

        name = []
        if getattr(sender, "first_name", None):
            name.append(sender.first_name)
        if getattr(sender, "last_name", None):
            name.append(sender.last_name)
        if getattr(sender, "title", None):
            sender_name = sender.title
        if getattr(sender, "username", None):
            sender_username = sender.username

        if not sender_name:
            sender_name = " ".join(name)

    text = msg.message or ""

    reactions = {}
    if getattr(msg, "reactions", None) and getattr(msg.reactions, "results", None):
        for r in msg.reactions.results:
            emoji = getattr(r.reaction, "emoticon", None)
            count = getattr(r, "count", 0)
            if emoji:
                reactions[emoji] = count

    mentions = []
    if getattr(msg, "entities", None):
        for e in msg.entities:
            if isinstance(e, MessageEntityMentionName):
                mention_text = text[e.offset : e.offset + e.length]
                mentions.append({"user_id": e.user_id, "text": mention_text})
            elif isinstance(e, MessageEntityMention):
                mention_text = text[e.offset : e.offset + e.length]
                mentions.append({"text": mention_text})

    reply_id = None
    if getattr(msg, "reply_to", None) and getattr(msg.reply_to, "reply_to_msg_id", None):
        reply_id = msg.reply_to.reply_to_msg_id

    return {
        "id": msg.id,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_username": sender_username,
        "text": clean_message_text(text),
        "reactions": reactions,
        "mentions": mentions,
        "reply_id": reply_id,
        "date": msg.date.isoformat(),
    }