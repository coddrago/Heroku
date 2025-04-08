# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import logging

import telethon
from telethon.tl.types import Message
from telethon import types, functions, extensions

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class Translator(loader.Module):
    """Translates text (obviously)"""

    strings = {"name": "Translator"}

    @loader.command()
    async def tr(self, message: Message):
        if not (args := utils.get_args_raw(message)):
            text = None
            lang = self.strings("language")
        else:
            lang = args.split(maxsplit=1)[0]
            if len(lang) != 2:
                text = args
                lang = self.strings("language")
            else:
                try:
                    text = args.split(maxsplit=1)[1]
                except IndexError:
                    text = None

        if not text:
            if not (reply := await message.get_reply_message()):
                await utils.answer(message, self.strings("no_args"))
                return

            text = reply.raw_text
            entities = reply.entities
        else:
            entities = []

        try:
            await utils.answer(
                message,
                await self.translate(
                    message.peer_id,
                    message,
                    lang,
                    raw_text=text,
                    entities=entities,
                ),
            )
        except Exception:
            logger.exception("Unable to translate text")
            await utils.answer(message, self.strings("error"))

    async def translate(self, peer, message, to_lang, raw_text, entities) -> str:
        msg_id = telethon.utils.get_message_id(message) or 0
        if not msg_id:
            return None

        if not isinstance(message, types.Message):
            message = (await self.get_messages(peer, ids=[msg_id]))[0]

        result = await self._client(
            functions.messages.TranslateTextRequest(
                peer=peer,
                id=[msg_id],
                text=[
                    types.TextWithEntities(
                        raw_text or message.raw_text,
                        entities or message.entities or [],
                    )
                ],
                to_lang=to_lang,
            )
        )

        return (
            extensions.html.unparse(
                result.result[0].text,
                result.result[0].entities,
            )
            if result and result.result
            else ""
        )