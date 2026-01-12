# ©️ Codrago, 2024-2030
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import contextlib
import io
import logging
import os
import re
import typing
from copy import deepcopy
from urllib.parse import urlparse

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramRetryAfter
from aiogram.types import (
    CallbackQuery,
    InputFile,
    InputMediaAnimation,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
)

from .. import utils

if typing.TYPE_CHECKING:
    from ..core import InlineManager

logger = logging.getLogger(__name__)


def sanitise_text(self: "InlineManager", text: str) -> str:
    return re.sub(r"</?emoji.*?>", "", text)


async def _edit_unit(
    self: "InlineManager",
    text: typing.Optional[str] = None,
    reply_markup: typing.Optional[typing.Any] = None,
    *,
    photo: typing.Optional[str] = None,
    file: typing.Optional[str] = None,
    video: typing.Optional[str] = None,
    audio: typing.Optional[typing.Union[dict, str]] = None,
    gif: typing.Optional[str] = None,
    mime_type: typing.Optional[str] = None,
    force_me: typing.Optional[bool] = None,
    disable_security: typing.Optional[bool] = None,
    always_allow: typing.Optional[typing.List[int]] = None,
    disable_web_page_preview: bool = True,
    query: typing.Optional[CallbackQuery] = None,
    unit_id: typing.Optional[str] = None,
    inline_message_id: typing.Optional[str] = None,
    chat_id: typing.Optional[int] = None,
    message_id: typing.Optional[int] = None,
) -> bool:
    """
    Edits unit message
    :param text: Text of message
    :param reply_markup: Inline keyboard
    :param photo: Url to a valid photo to attach to message
    :param file: Url to a valid file to attach to message
    :param video: Url to a valid video to attach to message
    :param audio: Url to a valid audio to attach to message
    :param gif: Url to a valid gif to attach to message
    :param mime_type: Mime type of file
    :param force_me: Allow only userbot owner to interact with buttons
    :param disable_security: Disable security check for buttons
    :param always_allow: List of user ids, which will always be allowed
    :param disable_web_page_preview: Disable web page preview
    :param query: Callback query
    :return: Status of edit
    """
    from .buttons import _validate_markup, _generate_markup

    reply_markup = _validate_markup(self, reply_markup) or []

    if text is not None and not isinstance(text, str):
        logger.error(
            "Invalid type for `text`. Expected `str`, got `%s`", type(text)
        )
        return False

    if file and not mime_type:
        logger.error(
            "You must pass `mime_type` along with `file` field\n"
            "It may be either 'application/zip' or 'application/pdf'"
        )
        return False

    if isinstance(audio, str):
        audio = {"url": audio}

    if isinstance(text, str):
        text = sanitise_text(self, text)

    media_params = [
        photo is None,
        gif is None,
        file is None,
        video is None,
        audio is None,
    ]

    if media_params.count(False) > 1:
        logger.error("You passed two or more exclusive parameters simultaneously")
        return False

    if unit_id is not None and unit_id in self._units:
        unit = self._units[unit_id]

        unit["buttons"] = reply_markup

        if isinstance(force_me, bool):
            unit["force_me"] = force_me

        if isinstance(disable_security, bool):
            unit["disable_security"] = disable_security

        if isinstance(always_allow, list):
            unit["always_allow"] = always_allow
    else:
        unit = {}

    if not chat_id or not message_id:
        inline_message_id = (
            inline_message_id
            or unit.get("inline_message_id", False)
            or getattr(query, "inline_message_id", None)
        )

    if not chat_id and not message_id and not inline_message_id:
        logger.warning(
            "Attempted to edit message with no `inline_message_id`. "
            "Possible reasons:\n"
            "- Form was sent without buttons and due to "
            "the limits of Telegram API can't be edited\n"
            "- There is an in-userbot error, which you should report"
        )
        return False

    try:
        path = urlparse(photo).path
        ext = os.path.splitext(path)[1]
    except Exception:
        ext = None

    if photo is not None and ext in {".gif", ".mp4"}:
        gif = deepcopy(photo)
        photo = None

    media = next(
        (media for media in [photo, file, video, audio, gif] if media), None
    )

    if isinstance(media, bytes):
        media = io.BytesIO(media)
        media.name = "upload.mp4"

    if isinstance(media, io.BytesIO):
        media = InputFile(filename=media)

    kind = (
        "file"
        if file
        else "photo"
        if photo
        else "audio"
        if audio
        else "video"
        if video
        else "gif"
        if gif
        else None
    )

    match kind:
        case "file":
            media = InputMediaDocument(media=media, caption=text, parse_mode="HTML")
        case "photo":
            media = InputMediaPhoto(media=media, caption=text, parse_mode="HTML")
        case "audio":
            if isinstance(audio, dict):
                media = InputMediaAudio(
                    media=audio["url"],
                    title=audio.get("title"),
                    performer=audio.get("performer"),
                    duration=audio.get("duration"),
                    caption=text,
                    parse_mode="HTML",
                )
            else:
                media = InputMediaAudio(
                    media=audio,
                    caption=text,
                    parse_mode="HTML",
                )
        case "video":
            media = InputMediaVideo(media=media, caption=text, parse_mode="HTML")
        case "gif":
            media = InputMediaAnimation(media=media, caption=text, parse_mode="HTML")

    if media is None and text is None and reply_markup:
        try:
            await self.bot.edit_message_reply_markup(
                **(
                    {"inline_message_id": inline_message_id}
                    if inline_message_id
                    else {"chat_id": chat_id, "message_id": message_id}
                ),
                reply_markup=_generate_markup(self, reply_markup),
            )
        except Exception:
            return False

        return True

    if media is None and text is None:
        logger.error("You must pass either `text` or `media` or `reply_markup`")
        return False

    if media is None:
        try:
            await self.bot.edit_message_text(
                text,
                **(
                    {"inline_message_id": inline_message_id}
                    if inline_message_id
                    else {"chat_id": chat_id, "message_id": message_id}
                ),
                disable_web_page_preview=disable_web_page_preview,
                reply_markup=_generate_markup(self, reply_markup)
                if isinstance(reply_markup, list)
                else unit.get("buttons", [])
            )
        except TelegramBadRequest as e:
            if "there is no text in the message to edit" not in str(e):
                raise

            try:
                await self.bot.edit_message_caption(
                    caption=text,
                    **(
                        {"inline_message_id": inline_message_id}
                        if inline_message_id
                        else {"chat_id": chat_id, "message_id": message_id}
                    ),
                    reply_markup=_generate_markup(self, reply_markup)
                    if isinstance(reply_markup, list)
                    else unit.get("buttons", [])
                )
            except Exception:
                return False
            else:
                return True
        except TelegramAPIError as e:
            if "message is not modified" in str(e):
                if query:
                    with contextlib.suppress(Exception):
                        await query.answer()
            elif "message to edit not found" in str(e):
                if query:
                    with contextlib.suppress(Exception):
                        await query.answer(
                            "I should have edited some message, but it is deleted :("
                        )

            return False
        except TelegramRetryAfter as e:
            logger.info("Sleeping %ss on aiogram FloodWait...", e.retry_after)
            await asyncio.sleep(e.retry_after)
            return await _edit_unit(self, **utils.get_kwargs())
            

            return False
        else:
            return True

    try:
        await self.bot.edit_message_media(
            **(
                {"inline_message_id": inline_message_id}
                if inline_message_id
                else {"chat_id": chat_id, "message_id": message_id}
            ),
            media=media,
            reply_markup=_generate_markup(self, reply_markup)
            if isinstance(reply_markup, list)
            else unit.get("buttons", [])
        )
    except TelegramRetryAfter as e:
        logger.info("Sleeping %ss on aiogram FloodWait...", e.retry_after)
        await asyncio.sleep(e.retry_after)
        return await _edit_unit(self, **utils.get_kwargs())
    except TelegramAPIError:
        if "message to edit not found" in str(e):
            if query:
                with contextlib.suppress(Exception):
                    await query.answer(
                        "I should have edited some message, but it is deleted :("
                    )
            return False
    else:
        return True