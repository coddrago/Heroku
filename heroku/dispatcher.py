"""Processes incoming events and dispatches them to appropriate handlers"""

# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

# ©️ Codrago, 2024-2030
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import collections
import contextlib
import copy
import inspect
import logging
import re
import sys
import traceback
import typing

import requests
from pyrogram import raw, types
from pyrogram.errors import FloodWait, RPCError
from pyrogram.enums import ChatType, MessageMediaType
from pyrogram.types import ChatEvent, ChatEventFilter, Message, ReplyParameters
from pyrogram.types.messages_and_media.message import Str

from . import loader, main, security, utils
from .database import Database
from .loader import Modules
from .tl_cache import CustomClient

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from .types import Command

# Keys for layout switch
_LAYOUT_TRANSLATION = str.maketrans(
    'ёйцукенгшщзхъфывапролджэячсмитьбю.Ё"№;%:?ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,'
    + "`qwertyuiop[]asdfghjkl;'zxcvbnm,./~@#$%^&QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?",
    
    "`qwertyuiop[]asdfghjkl;'zxcvbnm,./~@#$%^&QWERTYUIOP{}ASDFGHJKL:\"|ZXCVBNM<>?"
    + 'ёйцукенгшщзхъфывапролджэячсмитьбю.Ё"№;%:?ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭ/ЯЧСМИТЬБЮ,'
)

ALL_TAGS = [
    "no_commands",
    "only_commands",
    "out",
    "in",
    "only_messages",
    "editable",
    "no_media",
    "only_media",
    "only_photos",
    "only_videos",
    "only_audios",
    "only_docs",
    "only_stickers",
    "only_inline",
    "only_channels",
    "only_groups",
    "only_pm",
    "no_pm",
    "no_channels",
    "no_groups",
    "no_inline",
    "no_stickers",
    "no_docs",
    "no_audios",
    "no_videos",
    "no_photos",
    "no_forwards",
    "no_reply",
    "no_mention",
    "mention",
    "only_reply",
    "only_forwards",
    "startswith",
    "endswith",
    "contains",
    "regex",
    "filter",
    "from_id",
    "chat_id",
    "thumb_url",
    "alias",
    "aliases",
]


def _decrement_ratelimit(delay, data, key, severity):
    def inner():
        data[key] = max(0, data[key] - severity)

    asyncio.get_event_loop().call_later(delay, inner)


class CommandDispatcher:
    def __init__(
        self,
        modules: Modules,
        client: CustomClient,
        db: Database,
    ):
        self._modules = modules
        self._client = client
        self.client = client
        self._db = db

        self._ratelimit_storage_user = collections.defaultdict(int)
        self._ratelimit_storage_chat = collections.defaultdict(int)
        self._ratelimit_max_user = db.get(__name__, "ratelimit_max_user", 30)
        self._ratelimit_max_chat = db.get(__name__, "ratelimit_max_chat", 100)

        self.security = security.SecurityManager(client, db)

        self.check_security = self.security.check
        self._me = self._client.heroku_me.id
        self._cached_usernames = set()

        if self._client.heroku_me.username:
            self._cached_usernames.add(self._client.heroku_me.username.lower())

        if self._client.heroku_me.usernames:
            self._cached_usernames.update(
                u.username.lower()
                for u in getattr(self._client.heroku_me, "usernames", [])
            )

        self._cached_usernames.add(str(self._client.heroku_me.id))

        self.raw_handlers: list[Command] = []
        self._external_bl: typing.List[int] = []

        asyncio.ensure_future(self._external_bl_reload_loop())

    async def _handle_ratelimit(self, message: Message, func: callable) -> bool:
        if await self.security.check(message, security.OWNER):
            return True

        func = getattr(func, "__func__", func)
        ret = True
        chat = self._ratelimit_storage_chat[message.chat.id]

        if message.from_user.id:
            user = self._ratelimit_storage_user[message.chat.id]
            severity = (5 if getattr(func, "ratelimit", False) else 2) * (
                (user + chat) // 30 + 1
            )
            user += severity
            self._ratelimit_storage_user[message.chat.id] = user
            if user > self._ratelimit_max_user:
                ret = False
            else:
                self._ratelimit_storage_chat[message.chat.id] = chat

            _decrement_ratelimit(
                self._ratelimit_max_user * severity,
                self._ratelimit_storage_user,
                message.chat.id,
                severity,
            )
        else:
            severity = (5 if getattr(func, "ratelimit", False) else 2) * (
                chat // 15 + 1
            )

        chat += severity

        if chat > self._ratelimit_max_chat:
            ret = False

        _decrement_ratelimit(
            self._ratelimit_max_chat * severity,
            self._ratelimit_storage_chat,
            message.chat.id,
            severity,
        )

        return ret

    def _handle_grep(self, message: Message) -> Message: # TODO
        # Allow escaping grep with double stick
        if "||grep" in message.content.html or "|| grep" in message.content.html:
            message.raw_text = re.sub(r"\|\| ?grep", "| grep", message.raw_text)
            message.content = re.sub(r"\|\| ?grep", "| grep", message.content)
            message.message = re.sub(r"\|\| ?grep", "| grep", message.message)
            return message

        grep = False
        if not re.search(r".+\| ?grep (.+)", message.raw_text):
            return message

        grep = re.search(r".+\| ?grep (.+)", message.raw_text).group(1)
        message.content = re.sub(r"\| ?grep.+", "", message.content)
        message.raw_text = re.sub(r"\| ?grep.+", "", message.raw_text)
        message.message = re.sub(r"\| ?grep.+", "", message.message)

        ungrep = False

        if re.search(r"-v (.+)", grep):
            ungrep = re.search(r"-v (.+)", grep).group(1)
            grep = re.sub(r"(.+) -v .+", r"\g<1>", grep)

        grep = utils.escape_html(grep).strip() if grep else False
        ungrep = utils.escape_html(ungrep).strip() if ungrep else False

        old_edit = message.edit
        old_reply = message.reply
        old_respond = message.answer

        def process_text(text: str) -> str:
            nonlocal grep, ungrep
            res = []

            for line in text.split("\n"):
                if (
                    grep
                    and grep in utils.remove_html(line)
                    and (not ungrep or ungrep not in utils.remove_html(line))
                ):
                    res.append(
                        utils.remove_html(line, escape=True).replace(
                            grep, f"<u>{grep}</u>"
                        )
                    )

                if not grep and ungrep and ungrep not in utils.remove_html(line):
                    res.append(utils.remove_html(line, escape=True))

            cont = (
                (f"contain <b>{grep}</b>" if grep else "")
                + (" and" if grep and ungrep else "")
                + ((" do not contain <b>" + ungrep + "</b>") if ungrep else "")
            )

            if res:
                text = f"<i>💬 Lines that {cont}:</i>\n" + "\n".join(res)
            else:
                text = f"💬 <i>No lines that {cont}</i>"

            return text

        async def my_edit(text, *args, **kwargs):
            text = process_text(text)
            kwargs["parse_mode"] = "HTML"
            return await old_edit(text, *args, **kwargs)

        async def my_reply(text, *args, **kwargs):
            text = process_text(text)
            kwargs["parse_mode"] = "HTML"
            return await old_reply(text, *args, **kwargs)

        async def my_respond(text, *args, **kwargs):
            text = process_text(text)
            kwargs["parse_mode"] = "HTML"
            kwargs.setdefault("reply_parameters", ReplyParameters(message_id=utils.get_topic(message)))
            return await old_respond(text, *args, **kwargs)

        message.edit = my_edit
        message.reply = my_reply
        message.answer = my_respond
        message.heroku_grepped = True

        return message

    async def _handle_command(
        self,
        _message: "Message",
        watcher: bool = False,
    ) -> typing.Union[bool, typing.Tuple[Message, str, str, callable]]:
        logger.debug("handling command in message %s", _message)
        if not hasattr(_message, "text"):
            return False

        initiator = getattr(getattr(_message, "from_user", {}), "id", 0)

        main_prefix = self._db.get(main.__name__, "command_prefix", ".")
        if initiator == self._client.tg_id:
            prefix = main_prefix
        else:
            prefix = self._db.get(main.__name__, "command_prefixes", {})
            prefix = prefix.get(str(initiator), main_prefix)

        logger.debug("using \"%s\" prefix for msg_id=%s", prefix, _message.id)

        message = utils.msg_censor(_message)

        if not message.content:
            logger.debug("there is no text in message for chat_id=%s msg_id=%s", _message.chat.id, _message.id)
            return False
        
        message.text = message.content # just for easiest text editing

        if (
            message.outgoing
            and len(message.text) > len(prefix) * 2
            and (
                message.text.startswith(prefix * 2)
                and any(s != prefix for s in message.text)
                or message.text.startswith(str.translate(prefix * 2, _LAYOUT_TRANSLATION))
                and any(s != str.translate(prefix, _LAYOUT_TRANSLATION) for s in message.text)
            )
        ):
            # Allow escaping commands using .'s
            logger.debug("it is an escape! made it for chat_id=%s msg_id=%s", _message.chat.id, _message.id)
            if not watcher:
                await message.edit(
                    message.html_text[len(prefix):],
                )
            return False

        if (
            message.text.startswith(str.translate(prefix, _LAYOUT_TRANSLATION))
            and str.translate(prefix, _LAYOUT_TRANSLATION) != prefix
        ):
            logger.debug("it is keyboard switch for chat_id=%s msg_id=%s", _message.chat.id, _message.id)
            message.text = Str(str.translate(message.text, _LAYOUT_TRANSLATION)).init(message.entities)

        elif not message.text.startswith(prefix):
            return False

        if (
            message.sticker
            or message.dice
            # or message.audio # is there really a reason for this?
            or message.via_bot
        ):
            logger.debug("it is a non-editable message. returning for chat_id=%s msg_id=%s", _message.chat.id, _message.id)
            return False

        blacklist_chats = self._db.get(main.__name__, "blacklist_chats", [])
        whitelist_chats = self._db.get(main.__name__, "whitelist_chats", [])
        whitelist_modules = self._db.get(main.__name__, "whitelist_modules", [])

        # ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️
        # It's not recommended to remove the security check below (external_bl)
        # If you attempt to bypass this protection, you will be banned from the chat
        # The protection from using userbots is multi-layer and this is one of the layers
        # If you bypass it, the next (external) layer will trigger and you will be banned
        # ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

        if (
            (chat_id := message.chat.id) in self._external_bl
            or chat_id in blacklist_chats
            or (whitelist_chats and chat_id not in whitelist_chats)
        ):
            return False

        if not message.text or len(message.text.strip()) == len(prefix):
            logger.debug("message is just the prefix. returning for chat_id=%s msg_id=%s", _message.chat.id, _message.id)
            return False  # Message is just the prefix


        command = message.text[len(prefix):].strip().split(maxsplit=1)[0]
        tag = command.split("@", maxsplit=1)
        logger.debug(f"Received command: {command}")
        tag = command.split("@", maxsplit=1)
        logger.debug(f"Command tag: {tag}")

        if len(tag) == 2:
            if tag[1] == "me":
                if not message.outgoing:
                    return False
        elif (
            message.outgoing
            or message.mentioned
            and message.text is not None
            and not any(
                f"@{username}" in command.lower()
                for username in self._cached_usernames
            )
        ):
            pass
        elif (
            not message.chat.type == ChatType.PRIVATE
            and not self._db.get(main.__name__, "no_nickname", False)
            and command not in self._db.get(main.__name__, "nonickcmds", [])
            and initiator not in self._db.get(main.__name__, "nonickusers", [])
            and not self.security.check_tsec(initiator, command)
            and message.chat.id
            not in self._db.get(main.__name__, "nonickchats", [])
        ):
            return False

        logger.debug("dispatching da command for chat_id=%s msg_id=%s", _message.chat.id, _message.id)
        txt, func = self._modules.dispatch(tag[0])

        if (
            not func
            or not await self._handle_ratelimit(message, func)
            or not await self.security.check(
                message,
                func,
                usernames=self._cached_usernames,
            )
        ):
            logger.debug("not passed security check for chat_id=%s msg_id=%s", _message.chat.id, _message.id)
            return False

        if message.chat.type == ChatType.CHANNEL and message.edit_date:
            async for event in self._client.get_chat_event_log(
                chat_id,
                limit=10,
                filters=ChatEventFilter(edited_messages=True),
            ):
                if event.old_message.id == message.id:
                    if event.user.id != self._client.tg_id:
                        logger.debug("Ignoring edit in channel")
                        return False

                    break
            
            return False

        message.text = Str(prefix + txt + message.text[len(prefix + command) :])

        if (
            f"{str(chat_id)}.{func.__self__.__module__}" in blacklist_chats
            or whitelist_modules
            and f"{chat_id}.{func.__self__.__module__}" not in whitelist_modules
        ):
            return False

        if await self._handle_tags(_message, func):
            logger.debug("returned because the team did not pass the function conditions for chat_id=%s msg_id=%s", _message.chat.id, _message.id)
            return False

        if self._db.get(main.__name__, "grep", False) and not watcher:
            message = self._handle_grep(message)

        return message, prefix, txt, func

    async def handle_raw(self, _: CustomClient, event: "types.Update", users: list[types.User], chats: list[types.Chat]):
        """Handle raw events."""
        # print(type(event))
        for handler in self.raw_handlers:
            if isinstance(event, tuple(handler.updates)):
                try:
                    await loader._call_with_external_context(handler, event)
                except Exception as e:
                    logger.exception("Error in raw handler %s: %s", handler.id, e)

    async def handle_command(
        self,
        _: "CustomClient",
        event: "types.Message",
    ):
        """Handle all commands"""
        # print(type(event), event.text, event.id)
        message = await self._handle_command(event)
        if not message:
            logger.debug("not passed message for chat_id=%s msg_id=%s", event.chat.id, event.id)
            return

        message, _, _, func = message

        asyncio.ensure_future(
            self.future_dispatcher(
                func,
                message,
                self.command_exc,
            )
        )

    async def command_exc(self, _, message: Message):
        """Handle command exceptions."""
        exc = sys.exc_info()[1]
        logger.exception("Command failed", extra={"stack": inspect.stack()})
        if isinstance(exc, RPCError):
            if isinstance(exc, FloodWait):
                re_method = re.search(
                    r"\(caused by \"(\w+)\"\)",
                    str(exc)
                )

                if not re_method:
                    method = ""
                else:
                    method = re_method.group(1)

                hours = exc.value // 3600
                minutes = (exc.value % 3600) // 60
                seconds = exc.value % 60
                hours = f"{hours} hours, " if hours else ""
                minutes = f"{minutes} minutes, " if minutes else ""
                seconds = f"{seconds} seconds" if seconds else ""
                fw_time = f"{hours}{minutes}{seconds}"
                txt = (
                    self._client.loader.lookup("translations")
                    .strings("fw_error")
                    .format(
                        utils.escape_html(message.content),
                        fw_time,
                        method or "Unknown",
                    )
                )
            else:
                txt = (
                    "<tg-emoji emoji-id=5877477244938489129>🚫</tg-emoji> <b>Call"
                    f" </b><code>{utils.escape_html(message.content)}</code><b> failed"
                    " due to RPC (Telegram) error:</b>"
                    f" <code>{utils.escape_html(str(exc))}</code>"
                )
                txt = (
                    self._client.loader.lookup("translations")
                    .strings("rpc_error")
                    .format(
                        utils.escape_html(message.content),
                        utils.escape_html(str(exc)),
                    )
                )
        else:
            if not self._db.get(main.__name__, "inlinelogs", True):
                txt = (
                    "<tg-emoji emoji-id=5877477244938489129>🚫</tg-emoji><b> Call</b>"
                    f" <code>{utils.escape_html(message.content)}</code><b>"
                    " failed!</b>"
                )
            else:
                exc = "\n".join(traceback.format_exc().splitlines()[1:])
                txt = (
                    "<tg-emoji emoji-id=5877477244938489129>🚫</tg-emoji><b> Call</b>"
                    f" <code>{utils.escape_html(message.content)}</code><b>"
                    " failed!</b>\n\n<b>🧾 Logs:</b>\n<pre><code"
                    f' class="language-logs">{utils.escape_html(exc)}</code></pre>'
                )

        with contextlib.suppress(Exception):
            await (message.edit if message.outgoing else message.reply)(txt)

    async def watcher_exc(self, *_):
        logger.exception("Error running watcher", extra={"stack": inspect.stack()})

    async def _handle_tags(
        self,
        event: "Message",
        func: callable,
    ) -> bool:
        return bool(await self._handle_tags_ext(event, func))

    async def _handle_tags_ext(
        self,
        event: "Message",
        func: callable,
    ) -> str:
        """
        Handle tags.
        :param event: The message to handle.
        :param func: The function to handle.
        :return: The reason for the tag to fail.
        """
        m = event if isinstance(event, Message) else getattr(event, "message", event)

        reverse_mapping = {
            "out": lambda: getattr(m, "outgoing", True),
            "in": lambda: not getattr(m, "outgoing", True),
            "only_messages": lambda: isinstance(m, Message),
            "editable": (
                lambda: not getattr(m, "outgoing", False)
                and not getattr(m, "forward_origin", False)
                and not getattr(m, "sticker", False)
                and not getattr(getattr(m, "via_bot", False), "id", False)
            ),
            "no_media": lambda: (
                not isinstance(m, Message) or not getattr(m, "document", False)
            ),
            "only_media": lambda: isinstance(m, Message) and getattr(m, "document", False),
            "only_photos": lambda: m.media == MessageMediaType.PHOTO,
            "only_videos": lambda: m.media == MessageMediaType.VIDEO,
            "only_audios": lambda: m.media == MessageMediaType.AUDIO,
            "only_stickers": lambda: getattr(m, "sticker", False),
            "only_docs": lambda: m.media == MessageMediaType.DOCUMENT,
            "only_inline": lambda: getattr(getattr(m, "via_bot", False), "id", False),
            "only_channels": lambda: (
                getattr(m, "is_channel", False) and not getattr(m, "is_group", False)
            ),
            "no_channels": lambda: not getattr(m, "is_channel", False),
            "no_groups": (
                lambda: not getattr(m, "is_group", False)
                or getattr(m, "private", False)
                or getattr(m, "is_channel", False)
            ),
            "only_groups": (
                lambda: getattr(m, "is_group", False)
                or not getattr(m, "private", False)
                and not getattr(m, "is_channel", False)
            ),
            "no_pm": lambda: not getattr(m, "private", False),
            "only_pm": lambda: getattr(m, "private", False),
            "no_inline": lambda: not getattr(getattr(m, "via_bot", False), "id", False),
            "no_stickers": lambda: not getattr(m, "sticker", False),
            "no_docs": lambda: not m.media == MessageMediaType.DOCUMENT,
            "no_audios": lambda: not m.media == MessageMediaType.PHOTO,
            "no_videos": lambda: not m.media == MessageMediaType.VIDEO,
            "no_photos": lambda: not m.media == MessageMediaType.AUDIO,
            "no_forwards": lambda: not getattr(m, "forward_origin", False),
            "no_reply": lambda: not getattr(m, "reply_to_message_id", False),
            "only_forwards": lambda: getattr(m, "forward_origin", False),
            "only_reply": lambda: getattr(m, "reply_to_message_id", False),
            "mention": lambda: getattr(m, "mentioned", False),
            "no_mention": lambda: not getattr(m, "mentioned", False),
            "startswith": lambda: (
                isinstance(m, Message) and m.content.startswith(func.startswith)
            ),
            "endswith": lambda: (
                isinstance(m, Message) and m.content.endswith(func.endswith)
            ),
            "contains": lambda: isinstance(m, Message) and func.contains in m.content,
            "filter": lambda: callable(func.filter) and func.filter(m),
            "from_id": lambda: getattr(getattr(m, "from_user", None), "id", None) == func.from_id,
            "chat_id": lambda: m.chat.id
            == (
                func.chat_id
                if not str(func.chat_id).startswith("-100")
                else int(str(func.chat_id)[4:])
            ),
            "regex": lambda: (
                isinstance(m, Message) and re.search(func.regex, m.content)
            ),
        }

        return (
            "no_commands"
            if getattr(func, "no_commands", False)
            and await self._handle_command(event, watcher=True)
            else (
                "only_commands"
                if getattr(func, "only_commands", False)
                and not await self._handle_command(event, watcher=True)
                else next(
                    (
                        tag
                        for tag in ALL_TAGS
                        if getattr(func, tag, False)
                        and tag in reverse_mapping
                        and not reverse_mapping[tag]()
                    ),
                    None,
                )
            )
        )

    async def handle_incoming(
        self,
        _: "CustomClient",
        event: "Message",
    ):
        """Handle all incoming messages"""
        if isinstance(event, list): # deleted messages list # for what reason do we need to catch it?
            return

        message = utils.msg_censor(event)

        blacklist_chats = self._db.get(main.__name__, "blacklist_chats", [])
        whitelist_chats = self._db.get(main.__name__, "whitelist_chats", [])
        whitelist_modules = self._db.get(main.__name__, "whitelist_modules", [])

        # ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️
        # It's not recommended to remove the security check below (external_bl)
        # If you attempt to bypass this protection, you will be banned from the chat
        # The protection from using userbots is multi-layer and this is one of the layers
        # If you bypass it, the next (external) layer will trigger and you will be banned
        # ⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️

        if (
            (chat_id := message.chat.id) in self._external_bl
            or chat_id in blacklist_chats
            or (whitelist_chats and chat_id not in whitelist_chats)
        ):
            logger.debug("Message is blacklisted")
            return

        for func in self._modules.watchers:
            bl = self._db.get(main.__name__, "disabled_watchers", {})
            modname = str(func.__self__.__class__.strings["name"])

            if (
                modname in bl
                and isinstance(message, Message)
                and (
                    "*" in bl[modname]
                    or chat_id in bl[modname]
                    or "only_chats" in bl[modname]
                    and message.chat.type == ChatType.PRIVATE
                    or "only_pm" in bl[modname]
                    and not message.chat.type == ChatType.PRIVATE
                    or "out" in bl[modname]
                    and not message.outgoing
                    or "in" in bl[modname]
                    and message.outgoing
                )
                or f"{str(chat_id)}.{func.__self__.__module__}" in blacklist_chats
                or whitelist_modules
                and f"{str(chat_id)}.{func.__self__.__module__}"
                not in whitelist_modules
                or await self._handle_tags(event, func)
            ):
                continue

            # Avoid weird AttributeErrors in weird dochub modules by settings placeholder
            # of attributes
            for placeholder in {"text", "raw_text", "out"}:
                try:
                    if not hasattr(message, placeholder):
                        setattr(message, placeholder, "")
                except UnicodeDecodeError:
                    pass

            # Run watcher via ensure_future so in case user has a lot
            # of watchers with long actions, they can run simultaneously
            asyncio.ensure_future(
                self.future_dispatcher(
                    func,
                    message,
                    self.watcher_exc,
                )
            )

    async def future_dispatcher(
        self,
        func: callable,
        message: Message,
        exception_handler: callable,
        *args,
    ):
        # Will be used to determine, which client caused logging messages
        # parsed via inspect.stack()
        _heroku_client_id_logging_tag = copy.copy(self.client.tg_id)  # noqa: F841
        try:
            await loader._call_with_external_context(func, message)
        except Exception as e:
            await exception_handler(e, message, *args)

    async def _external_bl_reload_loop(self):
        while True:
            with contextlib.suppress(Exception):
                self._external_bl = (
                    await utils.run_sync(
                        requests.get,
                        "https://ubguard.codrago.life/blacklist.json",
                    )
                ).json()["blacklist"]

            await asyncio.sleep(60)
