
# ©️ Codrago, 2024-2025
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import atexit as _atexit
import contextlib
import functools
import inspect
import io
import json
import logging
import os
import random
import re
import shlex
import signal
import string
import time
import typing
from datetime import timedelta
from urllib.parse import urlparse
import emoji

import git
import grapheme
import herokutl
import herokutl.extensions
import herokutl.extensions.html
import requests
from aiogram.types import Message as AiogramMessage
from herokutl import hints
from herokutl.tl.custom.message import Message
from herokutl.tl.functions.account import UpdateNotifySettingsRequest
from herokutl.tl.functions.channels import (
    CreateChannelRequest,
    EditAdminRequest,
    EditPhotoRequest,
    InviteToChannelRequest,
)
from herokutl.tl.functions.messages import (
    GetDialogFiltersRequest,
    SetHistoryTTLRequest,
    UpdateDialogFilterRequest,
)
from herokutl.tl.types import (
    Channel,
    Chat,
    ChatAdminRights,
    InputDocument,
    InputPeerNotifySettings,
    MessageEntityBankCard,
    MessageEntityBlockquote,
    MessageEntityBold,
    MessageEntityBotCommand,
    MessageEntityCashtag,
    MessageEntityCode,
    MessageEntityEmail,
    MessageEntityHashtag,
    MessageEntityItalic,
    MessageEntityMention,
    MessageEntityMentionName,
    MessageEntityPhone,
    MessageEntityPre,
    MessageEntitySpoiler,
    MessageEntityStrike,
    MessageEntityTextUrl,
    MessageEntityUnderline,
    MessageEntityUnknown,
    MessageEntityUrl,
    MessageMediaPhoto,
    MessageMediaDocument,
    MessageMediaWebPage,
    PeerChannel,
    PeerChat,
    PeerUser,
    UpdateNewChannelMessage,
    User,
)

from ..._internal import fw_protect
from ...inline.types import BotInlineCall, InlineCall, InlineMessage
from ...tl_cache import CustomTelegramClient
from ...types import HerokuReplyMarkup, ListLike, Module

FormattingEntity = typing.Union[
    MessageEntityUnknown,
    MessageEntityMention,
    MessageEntityHashtag,
    MessageEntityBotCommand,
    MessageEntityUrl,
    MessageEntityEmail,
    MessageEntityBold,
    MessageEntityItalic,
    MessageEntityCode,
    MessageEntityPre,
    MessageEntityTextUrl,
    MessageEntityMentionName,
    MessageEntityPhone,
    MessageEntityCashtag,
    MessageEntityUnderline,
    MessageEntityStrike,
    MessageEntityBlockquote,
    MessageEntityBankCard,
    MessageEntitySpoiler,
]

emoji_pattern = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport & map symbols
    "\U0001f1e0-\U0001f1ff"  # flags (iOS)
    "]+",
    flags=re.UNICODE,
)

parser = herokutl.utils.sanitize_parse_mode("html")
logger = logging.getLogger(__name__)

def get_lang_flag(countrycode: str) -> str:
    """
    Gets an emoji of specified countrycode
    :param countrycode: 2-letter countrycode
    :return: Emoji flag
    """
    if (
        len(
            code := [
                c
                for c in countrycode.lower()
                if c in string.ascii_letters + string.digits
            ]
        )
        == 2
    ):
        return "".join([chr(ord(c.upper()) + (ord("🇦") - ord("A"))) for c in code])

    return countrycode


def get_entity_url(
    entity: typing.Union[User, Channel],
    openmessage: bool = False,
) -> str:
    """
    Get link to object, if available
    :param entity: Entity to get url of
    :param openmessage: Use tg://openmessage link for users
    :return: Link to object or empty string
    """
    return (
        (
            f"tg://openmessage?id={entity.id}"
            if openmessage
            else f"tg://user?id={entity.id}"
        )
        if isinstance(entity, User)
        else (
            f"tg://resolve?domain={entity.username}"
            if getattr(entity, "username", None)
            else ""
        )
    )

def remove_emoji(text: str) -> str:

    """
    Removes all emoji from text
    """

    allchars = [str for str in text]
    emoji_list = [c for c in allchars if c in emoji.EMOJI_DATA]
    clean_text = ''.join([str for str in text if not any(i in str for i in emoji_list)])
    return clean_text


def remove_html(text: str, escape: bool = False, keep_emojis: bool = False) -> str:
    """
    Removes HTML tags from text
    :param text: Text to remove HTML from
    :param escape: Escape HTML
    :param keep_emojis: Keep custom emojis
    :return: Text without HTML
    """
    return (escape_html if escape else str)(
        re.sub(
            (
                r"(<\/?a.*?>|<\/?b>|<\/?i>|<\/?u>|<\/?strong>|<\/?em>|<\/?code>|<\/?strike>|<\/?del>|<\/?pre.*?>|<\/?blockquote.*?>)"
                if keep_emojis
                else r"(<\/?a.*?>|<\/?b>|<\/?i>|<\/?u>|<\/?strong>|<\/?em>|<\/?code>|<\/?strike>|<\/?del>|<\/?pre.*?>|<\/?emoji.*?>|<\/?blockquote.*?>)"
            ),
            "",
            text,
        )
    )

def check_url(url: str) -> bool:
    """
    Statically checks url for validity
    :param url: URL to check
    :return: True if valid, False otherwise
    """
    try:
        return bool(urlparse(url).netloc)
    except Exception:
        return False

def get_link(user: typing.Union[User, Channel], /) -> str:
    """
    Get telegram permalink to entity
    :param user: User or channel
    :return: Link to entity
    """
    return (
        f"tg://user?id={user.id}"
        if isinstance(user, User)
        else (
            f"tg://resolve?domain={user.username}"
            if getattr(user, "username", None)
            else ""
        )
    )


async def asset_channel(
    client: CustomTelegramClient,
    title: str,
    description: str,
    *,
    channel: bool = False,
    silent: bool = False,
    archive: bool = False,
    invite_bot: bool = False,
    avatar: typing.Optional[str] = None,
    ttl: typing.Optional[int] = None,
    forum: bool = False,
    _folder: typing.Optional[str] = None,
) -> typing.Tuple[Channel, bool]:
    """
    Create new channel (if needed) and return its entity
    :param client: Telegram client to create channel by
    :param title: Channel title
    :param description: Description
    :param channel: Whether to create a channel or supergroup
    :param silent: Automatically mute channel
    :param archive: Automatically archive channel
    :param invite_bot: Add inline bot and assure it's in chat
    :param avatar: Url to an avatar to set as pfp of created peer
    :param ttl: Time to live for messages in channel
    :param forum: Whether to create a forum channel
    :return: Peer and bool: is channel new or pre-existent
    """
    if not hasattr(client, "_channels_cache"):
        client._channels_cache = {}

    if (
        title in client._channels_cache
        and client._channels_cache[title]["exp"] > time.time()
    ):
        return client._channels_cache[title]["peer"], False

    # legacy heroku / hikka chats conversion to heroku
    if title.startswith("hikka-"):
        title = title.replace("hikka-", "heroku-")

    async for d in client.iter_dialogs():
        if d.title == title:
            client._channels_cache[title] = {"peer": d.entity, "exp": int(time.time())}
            if invite_bot:
                if all(
                    participant.id != client.loader.inline.bot_id
                    for participant in (
                        await client.get_participants(d.entity, limit=100)
                    )
                ):
                    await fw_protect()
                    await invite_inline_bot(client, d.entity)

            return d.entity, False

    await fw_protect()

    peer = (
        await client(
            CreateChannelRequest(
                title,
                description,
                megagroup=not channel,
                forum=forum,
            )
        )
    ).chats[0]

    if invite_bot:
        await fw_protect()
        await invite_inline_bot(client, peer)

    if silent:
        await fw_protect()
        await dnd(client, peer, archive)
    elif archive:
        await fw_protect()
        await client.edit_folder(peer, 1)

    if avatar:
        await fw_protect()
        await set_avatar(client, peer, avatar)

    if ttl:
        await fw_protect()
        await client(SetHistoryTTLRequest(peer=peer, period=ttl))

    if _folder:
        if _folder != "heroku":
            raise NotImplementedError

        folders = await client(GetDialogFiltersRequest())

        try:
            folder = next(folder for folder in folders if folder.title == "heroku")
        except Exception:
            folder = None

        if folder is not None and not any(
            peer.id == getattr(folder_peer, "channel_id", None)
            for folder_peer in folder.include_peers
        ):
            folder.include_peers += [await client.get_input_entity(peer)]

            await client(
                UpdateDialogFilterRequest(
                    folder.id,
                    folder,
                )
            )

    client._channels_cache[title] = {"peer": peer, "exp": int(time.time())}
    return peer, True

async def set_avatar(
    client: CustomTelegramClient,
    peer: hints.Entity,
    avatar: str,
) -> bool:
    """
    Sets an entity avatar
    :param client: Client to use
    :param peer: Peer to set avatar to
    :param avatar: Avatar to set
    :return: True if avatar was set, False otherwise
    """
    if isinstance(avatar, str) and check_url(avatar):
        f = (
            await run_sync(
                requests.get,
                avatar,
            )
        ).content
    elif isinstance(avatar, bytes):
        f = avatar
    else:
        return False

    await fw_protect()
    res = await client(
        EditPhotoRequest(
            channel=peer,
            photo=await client.upload_file(f, file_name="photo.png"),
        )
    )

    await fw_protect()

    try:
        await client.delete_messages(
            peer,
            message_ids=[
                next(
                    update
                    for update in res.updates
                    if isinstance(update, UpdateNewChannelMessage)
                ).message.id
            ],
        )
    except Exception:
        pass

    return True

async def get_target(message: Message, arg_no: int = 0) -> typing.Optional[int]:
    """
    Get target from message
    :param message: Message to get target from
    :param arg_no: Argument number to get target from
    :return: Target
    """

    if any(
        isinstance(entity, MessageEntityMentionName)
        for entity in (message.entities or [])
    ):
        e = sorted(
            filter(lambda x: isinstance(x, MessageEntityMentionName), message.entities),
            key=lambda x: x.offset,
        )[0]
        return e.user_id

    if len(get_args(message)) > arg_no:
        user = get_args(message)[arg_no]
    elif message.is_reply:
        return (await message.get_reply_message()).sender_id
    elif hasattr(message.peer_id, "user_id"):
        user = message.peer_id.user_id
    else:
        return None

    try:
        entity = await message.client.get_entity(user)
    except ValueError:
        return None
    else:
        if isinstance(entity, User):
            return entity.id

async def get_user(message: Message) -> typing.Optional[User]:
    """
    Get user who sent message, searching if not found easily
    :param message: Message to get user from
    :return: User who sent message
    """
    try:
        return await message.get_sender()
    except ValueError:  # Not in database. Lets go looking for them.
        logger.debug("User not in session cache. Searching...")

    if isinstance(message.peer_id, PeerUser):
        await message.client.get_dialogs()
        return await message.get_sender()

    if isinstance(message.peer_id, (PeerChannel, PeerChat)):
        async for user in message.client.iter_participants(
            message.peer_id,
            aggressive=True,
        ):
            if user.id == message.sender_id:
                return user

        logger.error("User isn't in the group where they sent the message")
        return None

    logger.error("`peer_id` is not a user, chat or channel")
    return None

def get_chat_id(message: typing.Union[Message, AiogramMessage]) -> int:
    """
    Get the chat ID, but without -100 if its a channel
    :param message: Message to get chat ID from
    :return: Chat ID
    """
    return herokutl.utils.resolve_id(
        getattr(message, "chat_id", None)
        or getattr(getattr(message, "chat", None), "id", None)
    )[0]


def get_entity_id(entity: hints.Entity) -> int:
    """
    Get entity ID
    :param entity: Entity to get ID from
    :return: Entity ID
    """
    return herokutl.utils.get_peer_id(entity)


def escape_html(text: str, /) -> str:  # sourcery skip
    """
    Pass all untrusted/potentially corrupt input here
    :param text: Text to escape
    :return: Escaped text
    """
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def escape_quotes(text: str, /) -> str:
    """
    Escape quotes to html quotes
    :param text: Text to escape
    :return: Escaped text
    """
    return escape_html(text).replace('"', "&quot;")


def relocate_entities(
    entities: typing.List[FormattingEntity],
    offset: int,
    text: typing.Optional[str] = None,
) -> typing.List[FormattingEntity]:
    """
    Move all entities by offset (truncating at text)
    :param entities: List of entities
    :param offset: Offset to move by
    :param text: Text to truncate at
    :return: List of entities
    """
    length = len(text) if text is not None else 0

    for ent in entities.copy() if entities else ():
        ent.offset += offset
        if ent.offset < 0:
            ent.length += ent.offset
            ent.offset = 0
        if text is not None and ent.offset + ent.length > length:
            ent.length = length - ent.offset
        if ent.length <= 0:
            entities.remove(ent)

    return entities

def find_caller(
    stack: typing.Optional[typing.List[inspect.FrameInfo]] = None,
) -> typing.Any:
    """
    Attempts to find command in stack
    :param stack: Stack to search in
    :return: Command-caller or None
    """
    caller = next(
        (
            frame_info
            for frame_info in stack or inspect.stack()
            if hasattr(frame_info, "function")
            and any(
                inspect.isclass(cls_)
                and issubclass(cls_, Module)
                and cls_ is not Module
                for cls_ in frame_info.frame.f_globals.values()
            )
        ),
        None,
    )

    if not caller:
        return next(
            (
                frame_info.frame.f_locals["func"]
                for frame_info in stack or inspect.stack()
                if hasattr(frame_info, "function")
                and frame_info.function == "future_dispatcher"
                and (
                    "CommandDispatcher"
                    in getattr(getattr(frame_info, "frame", None), "f_globals", {})
                )
            ),
            None,
        )

    return next(
        (
            getattr(cls_, caller.function, None)
            for cls_ in caller.frame.f_globals.values()
            if inspect.isclass(cls_) and issubclass(cls_, Module)
        ),
        None,
    )

async def dnd(
    client: CustomTelegramClient,
    peer: hints.Entity,
    archive: bool = True,
) -> bool:
    """
    Mutes and optionally archives peer
    :param peer: Anything entity-link
    :param archive: Archive peer, or just mute?
    :return: `True` on success, otherwise `False`
    """
    try:
        await client(
            UpdateNotifySettingsRequest(
                peer=peer,
                settings=InputPeerNotifySettings(
                    show_previews=False,
                    silent=True,
                    mute_until=2**31 - 1,
                ),
            )
        )

        if archive:
            await fw_protect()
            await client.edit_folder(peer, 1)
    except Exception:
        logger.exception("utils.dnd error")
        return False

    return True