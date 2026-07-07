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

import logging
import typing

from pyrogram.enums import ParseMode
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent
from pyrogram.types import Message as _PyrogramMessage

HerokuReplyMarkup = typing.Union[typing.List[typing.List[dict]], typing.List[dict], dict]

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from .core import InlineManager


class InlineMessage:
    """Message, sent via inline bot"""

    def __init__(
        self,
        inline_manager: "InlineManager",  # type: ignore  # noqa: F821
        unit_id: str,
        inline_message_id: str,
    ):
        self.inline_message_id = inline_message_id
        self.unit_id = unit_id
        self.inline_manager = inline_manager
        self._units = inline_manager._units
        self.form = (
            {"id": unit_id, **self._units[unit_id]} if unit_id in self._units else {}
        )

    async def edit(self, *args, **kwargs) -> "InlineMessage":
        if "unit_id" in kwargs:
            kwargs.pop("unit_id")

        if "inline_message_id" in kwargs:
            kwargs.pop("inline_message_id")

        return await self.inline_manager._edit_unit(
            *args,
            unit_id=self.unit_id,
            inline_message_id=self.inline_message_id,
            **kwargs,
        )

    async def delete(self) -> bool:
        entity = self._units.get(self.unit_id)
        if not entity:
            return await self.original_call.answer("msg not found", show_alert=True)

        msgid = entity.get("message_id")
        cid = entity.get("chat")

        await self.inline_manager._client.delete_messages(cid, msgid)
        if hasattr(self, "original_call"):
            return await self.original_call.answer("")

    async def unload(self) -> bool:
        return await self.inline_manager._unload_unit(unit_id=self.unit_id)


class BotInlineMessage:
    """Message, sent through inline bot itself"""

    def __init__(
        self,
        inline_manager: "InlineManager",  # type: ignore  # noqa: F821
        unit_id: str,
        chat_id: int,
        message_id: int,
    ):
        self.chat_id = chat_id
        self.unit_id = unit_id
        self.inline_manager = inline_manager
        self.message_id = message_id
        self._units = inline_manager._units
        self.form = (
            {"id": unit_id, **self._units[unit_id]} if unit_id in self._units else {}
        )

    async def edit(self, *args, **kwargs) -> "BotInlineMessage":
        if "unit_id" in kwargs:
            kwargs.pop("unit_id")

        if "message_id" in kwargs:
            kwargs.pop("message_id")

        if "chat_id" in kwargs:
            kwargs.pop("chat_id")

        return await self.inline_manager._edit_unit(
            *args,
            unit_id=self.unit_id,
            chat_id=self.chat_id,
            message_id=self.message_id,
            **kwargs,
        )

    async def delete(self) -> bool:
        return await self.inline_manager._delete_unit_message(
            self,
            unit_id=self.unit_id,
            chat_id=self.chat_id,
            message_id=self.message_id,
        )

    async def unload(self, *args, **kwargs) -> bool:
        if "unit_id" in kwargs:
            kwargs.pop("unit_id")

        return await self.inline_manager._unload_unit(
            *args,
            unit_id=self.unit_id,
            **kwargs,
        )


class _RawProxyMixin:
    """
    Delegates unknown attribute access to the wrapped raw pyrogram object.
    Unlike aiogram's pydantic models, pyrogram objects are plain, already
    `client`-bound instances, so their bound methods (`.answer()`,
    `.edit_message_text()`, ...) work as-is without any rebinding trick.
    """

    def __getattr__(self, name):
        return getattr(self._raw, name)


class InlineCall(_RawProxyMixin, InlineMessage):
    """Callback query that came from a message sent via inline mode"""

    def __init__(
        self,
        call,
        inline_manager: "InlineManager",  # type: ignore  # noqa: F821
        unit_id: str,
    ):
        self._raw = call
        self.original_call = call

        InlineMessage.__init__(
            self,
            inline_manager,
            unit_id,
            call.inline_message_id,
        )


class BotInlineCall(_RawProxyMixin, BotInlineMessage):
    """Callback query that came from a message the bot sent directly"""

    def __init__(
        self,
        call,
        inline_manager: "InlineManager",  # type: ignore  # noqa: F821
        unit_id: str,
    ):
        self._raw = call
        self.original_call = call

        BotInlineMessage.__init__(
            self,
            inline_manager,
            unit_id,
            call.message.chat.id,
            call.message.id,
        )


class InlineUnit:
    """InlineManager extension type. For internal use only"""

    def __init__(self):
        """Made just for type specification"""


class BotMessage(_PyrogramMessage):
    """Message sent/received through the inline bot's pyrogram client"""


class InlineQuery(_RawProxyMixin):
    """Wraps a pyrogram `InlineQuery`, adding Heroku's canned error responders"""

    def __init__(self, inline_query):
        self._raw = inline_query
        self.inline_query = inline_query
        query = inline_query.query or ""
        self.args = (
            query.split(maxsplit=1)[1] if len(query.split()) > 1 else ""
        )

    @staticmethod
    def _get_res(title: str, description: str, thumbnail_url: str) -> list:
        from ..utils.other import rand
        return [
            InlineQueryResultArticle(
                id=rand(20),
                title=title,
                description=description,
                input_message_content=InputTextMessageContent(
                    message_text="😶‍🌫️ <i>There is nothing here...</i>",
                    parse_mode=ParseMode.HTML,
                ),
                thumb_url=thumbnail_url,
                thumb_width=128,
                thumb_height=128,
            )
        ]

    async def e400(self):
        await self.answer(
            self._get_res(
                title="🚫 400",
                description=(
                    "Bad request. You need to pass right arguments, follow module's"
                    " documentation"
                ),
                thumbnail_url="https://img.icons8.com/color/344/swearing-male--v1.png",
            ),
            cache_time=0,
        )

    async def e403(self):
        await self.answer(
            self._get_res(
                title="🚫 403",
                description="You have no permissions to access this result",
                thumbnail_url="https://img.icons8.com/external-wanicon-flat-wanicon/344/external-forbidden-new-normal-wanicon-flat-wanicon.png",
            ),
            cache_time=0,
        )

    async def e404(self):
        await self.answer(
            self._get_res(
                title="🚫 404",
                description="No results found",
                thumbnail_url="https://img.icons8.com/external-justicon-flat-justicon/344/external-404-error-responsive-web-design-justicon-flat-justicon.png",
            ),
            cache_time=0,
        )

    async def e426(self):
        await self.answer(
            self._get_res(
                title="🚫 426",
                description="You need to update Heroku before sending this request",
                thumbnail_url="https://img.icons8.com/fluency/344/approve-and-update.png",
            ),
            cache_time=0,
        )

    async def e500(self):
        await self.answer(
            self._get_res(
                title="🚫 500",
                description="Internal userbot error while processing request. More info in logs",
                thumbnail_url="https://img.icons8.com/external-vitaliy-gorbachev-flat-vitaly-gorbachev/344/external-error-internet-security-vitaliy-gorbachev-flat-vitaly-gorbachev.png",
            ),
            cache_time=0,
        )
