# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

# ©️ Codrago, 2024-2025
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import aiohttp
import contextlib
import functools
import io
import itertools
import logging
import os
import re
import typing
from copy import deepcopy
from urllib.parse import urlparse, unquote

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    WebAppInfo,
    CopyTextButton,
    InputMediaAnimation,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
)
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramAPIError,
    TelegramRetryAfter,
)
from herokutl.tl.functions.messages import RequestWebViewRequest

from .. import utils
from ..types import HerokuReplyMarkup
from .types import InlineCall, InlineUnit

if typing.TYPE_CHECKING:
    from ..inline.core import InlineManager

logger = logging.getLogger(__name__)

headers = {
  "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
  "accept": "application/json, text/javascript, */*; q=0.01",
  "referer": "https://webappinternal.telegram.org/botfather",
  "cookie": "stel_ln=ru",
}
HASH_PATTERN = re.compile(r"Main\.init\('([0-9a-f]{18})'\);")
BOT_ID_PATTERN = (
    r"<a class=\"tm-row tm-row-link\" href=\"/botfather/bot/(\d+)\">"
    r"<img class=\"tm-row-pic tm-row-pic-user\" src=\"https:\/\/cdn4\.telesco\.pe\/file\/[A-Za-z0-9_-]+\.jpg\">"
    r"<div> <div class=\"tm-row-value\">((?:(?!<\/div>).)*)<\/div>"
    r"<div class=\"tm-row-description\">@{}</div> </div></a>"
)
BOT_BASE_PATTERN = re.compile(BOT_ID_PATTERN.format(r"\w*_[0-9a-zA-Z]{6}_bot"))


class Utils(InlineUnit):
    def _generate_markup(
        self: "InlineManager",
        markup_obj: typing.Optional[typing.Union[HerokuReplyMarkup, str]],
    ) -> typing.Optional[InlineKeyboardMarkup]:
        """Generate markup for form or list of `dict`s"""
        if not markup_obj:
            return None

        if isinstance(markup_obj, InlineKeyboardMarkup):
            return markup_obj

        markup = InlineKeyboardMarkup(inline_keyboard=[])

        map_ = (
            self._units[markup_obj]["buttons"]
            if isinstance(markup_obj, str)
            else markup_obj
        )

        map_ = self._normalize_markup(map_)

        setup_callbacks = False

        for row in map_:
            for button in row:
                if not isinstance(button, dict):
                    logger.error(
                        "Button %s is not a `dict`, but `%s` in %s",
                        button,
                        type(button),
                        map_,
                    )
                    return None

                if "callback" not in button:
                    if button.get("action") == "close":
                        button["callback"] = self._close_unit_handler

                    if button.get("action") == "unload":
                        button["callback"] = self._unload_unit_handler

                    if button.get("action") == "answer":
                        if not button.get("message"):
                            logger.error(
                                "Button %s has no `message` to answer with", button
                            )
                            return None

                        button["callback"] = functools.partial(
                            self._answer_unit_handler,
                            show_alert=button.get("show_alert", False),
                            text=button["message"],
                        )

                if "callback" in button and "_callback_data" not in button:
                    button["_callback_data"] = utils.rand(30)
                    setup_callbacks = True

                if "input" in button and "_switch_query" not in button:
                    button["_switch_query"] = utils.rand(10)

        for row in map_:
            line = []
            for button in row:
                try:
                    if "url" in button:
                        if not utils.check_url(button["url"]):
                            logger.warning(
                                "Button have not been added to form, "
                                "because its url is invalid"
                            )
                            continue

                        line += [
                            InlineKeyboardButton(
                                text=str(button["text"]),
                                url=button["url"],
                            )
                        ]
                    elif "callback" in button:
                        line += [
                            InlineKeyboardButton(
                                text=str(button["text"]),
                                callback_data=button["_callback_data"],
                            )
                        ]
                        if setup_callbacks:
                            self._custom_map[button["_callback_data"]] = {
                                "handler": button["callback"],
                                **(
                                    {"always_allow": button["always_allow"]}
                                    if button.get("always_allow", False)
                                    else {}
                                ),
                                **(
                                    {"args": button["args"]}
                                    if button.get("args", False)
                                    else {}
                                ),
                                **(
                                    {"kwargs": button["kwargs"]}
                                    if button.get("kwargs", False)
                                    else {}
                                ),
                                **(
                                    {"force_me": True}
                                    if button.get("force_me", False)
                                    else {}
                                ),
                                **(
                                    {"disable_security": True}
                                    if button.get("disable_security", False)
                                    else {}
                                ),
                            }
                    elif "input" in button:
                        line += [
                            InlineKeyboardButton(
                                text=str(button["text"]),
                                switch_inline_query_current_chat=button["_switch_query"]
                                + " ",
                            )
                        ]
                    elif "data" in button:
                        line += [
                            InlineKeyboardButton(
                                text=str(button["text"]),
                                callback_data=button["data"],
                            )
                        ]
                    elif "web_app" in button:
                        line += [
                            InlineKeyboardButton(
                                text=str(button["text"]),
                                web_app=WebAppInfo(button["data"]),
                            )
                        ]

                    elif "copy" in button:
                        line += [
                            InlineKeyboardButton(
                                text=str(button["text"]),
                                copy_text=CopyTextButton(
                                    text=button["copy"]
                                )
                            )
                        ]
                        
                    elif "switch_inline_query_current_chat" in button:
                        line += [
                            InlineKeyboardButton(
                                text=str(button["text"]),
                                switch_inline_query_current_chat=button[
                                    "switch_inline_query_current_chat"
                                ],
                            )
                        ]
                    elif "switch_inline_query" in button:
                        line += [
                            InlineKeyboardButton(
                                text=str(button["text"]),
                                switch_inline_query_current_chat=button[
                                    "switch_inline_query"
                                ],
                            )
                        ]
                    else:
                        logger.warning(
                            (
                                "Button have not been added to "
                                "form, because it is not structured "
                                "properly. %s"
                            ),
                            button,
                        )
                except KeyError:
                    logger.exception(
                        "Error while forming markup! Probably, you "
                        "passed wrong type combination for button. "
                        "Contact developer of module."
                    )
                    return False

            markup.inline_keyboard.append(line)

        return markup

    generate_markup = _generate_markup

    async def _close_unit_handler(self: "InlineManager", call: InlineCall):
        return await self._client.delete_messages(call._units.get(call.unit_id).get('chat'), call._units.get(call.unit_id).get('message_id'))

    async def _unload_unit_handler(self: "InlineManager", call: InlineCall):
        await call.unload()

    async def _answer_unit_handler(self: "InlineManager", call: InlineCall, text: str, show_alert: bool):
        await call.answer(text, show_alert=show_alert)

    def _reverse_method_lookup(self: "InlineManager", needle: callable, /) -> typing.Optional[str]:
        return next(
            (
                name
                for name, method in itertools.chain(
                    self._allmodules.inline_handlers.items(),
                    self._allmodules.callback_handlers.items(),
                )
                if method == needle
            ),
            None,
        )

    async def check_inline_security(self: "InlineManager", *, func: typing.Callable, user: int) -> bool:
        """Checks if user with id `user` is allowed to run function `func`"""
        return await self._client.dispatcher.security.check(
            message=None,
            func=func,
            user_id=user,
            inline_cmd=self._reverse_method_lookup(func),
        )

    def _find_caller_sec_map(self: "InlineManager") -> typing.Optional[typing.Callable[[], int]]:
        try:
            caller = utils.find_caller()
            if not caller:
                return None

            logger.debug("Found caller: %s", caller)

            return lambda: self._client.dispatcher.security.get_flags(
                getattr(caller, "__self__", caller),
            )
        except Exception:
            logger.debug("Can't parse security mask in form", exc_info=True)

        return None

    def _normalize_markup(
        self: "InlineManager", reply_markup: HerokuReplyMarkup
    ) -> typing.List[typing.List[typing.Dict[str, typing.Any]]]:
        if isinstance(reply_markup, dict):
            return [[reply_markup]]

        if isinstance(reply_markup, list) and any(
            isinstance(i, dict) for i in reply_markup
        ):
            return [reply_markup]

        return reply_markup

    def sanitise_text(self: "InlineManager", text: str) -> str:
        return re.sub(r"</?emoji.*?>", "", text)

    async def _edit_unit(
        self: "InlineManager",
        text: typing.Optional[str] = None,
        reply_markup: typing.Optional[HerokuReplyMarkup] = None,
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
        reply_markup = self._validate_markup(reply_markup) or []

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
            text = self.sanitise_text(text)

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

        if file:
            media = InputMediaDocument(media=media, caption=text, parse_mode="HTML")
        elif photo:
            media = InputMediaPhoto(media=media, caption=text, parse_mode="HTML")
        elif audio:
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
        elif video:
            media = InputMediaVideo(media=media, caption=text, parse_mode="HTML")
        elif gif:
            media = InputMediaAnimation(media=media, caption=text, parse_mode="HTML")

        if media is None and text is None and reply_markup:
            try:
                await self.bot.edit_message_reply_markup(
                    **(
                        {"inline_message_id": inline_message_id}
                        if inline_message_id
                        else {"chat_id": chat_id, "message_id": message_id}
                    ),
                    reply_markup=self.generate_markup(reply_markup),
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
                    reply_markup=self.generate_markup(
                        reply_markup
                        if isinstance(reply_markup, list)
                        else unit.get("buttons", [])
                    ),
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
                        reply_markup=self.generate_markup(
                            reply_markup
                            if isinstance(reply_markup, list)
                            else unit.get("buttons", [])
                        ),
                    )
                except Exception:
                    return False
                else:
                    return True
            except TelegramAPIError as e:
                if True: # TODO "" in e.message
                    if query:
                        with contextlib.suppress(Exception):
                            await query.answer()
                elif True: # TODO "" in e.message
                    with contextlib.suppress(Exception):
                        await query.answer(
                            "I should have edited some message, but it is deleted :("
                        )

                return False
            except TelegramRetryAfter as e:
                logger.info("Sleeping %ss on aiogram FloodWait...", e.retry_after)
                await asyncio.sleep(e.retry_after)
                return await self._edit_unit(**utils.get_kwargs())
                

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
                reply_markup=self.generate_markup(
                    reply_markup
                    if isinstance(reply_markup, list)
                    else unit.get("buttons", [])
                ),
            )
        except TelegramRetryAfter as e:
            logger.info("Sleeping %ss on aiogram FloodWait...", e.retry_after)
            await asyncio.sleep(e.retry_after)
            return await self._edit_unit(**utils.get_kwargs())
        except TelegramAPIError:
            if True: # TODO
                with contextlib.suppress(Exception):
                    await query.answer(
                        "I should have edited some message, but it is deleted :("
                    )
                return False
        else:
            return True

    async def _delete_unit_message(
        self: "InlineManager",
        call: typing.Optional[CallbackQuery] = None,
        unit_id: typing.Optional[str] = None,
        chat_id: typing.Optional[int] = None,
        message_id: typing.Optional[int] = None,
    ) -> bool:
        """Params `self`, `unit_id` are for internal use only, do not try to pass them"""
        if getattr(getattr(call, "message", None), "chat", None):
            try:
                await self.bot.delete_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                )
            except Exception:
                return False

            return True

        if chat_id and message_id:
            try:
                await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception:
                return False

            return True

        if not unit_id and hasattr(call, "unit_id") and call.unit_id:
            unit_id = call.unit_id

        try:
            await self._client.delete_messages(call._units.get(unit_id).get('chat'), call._units.get(unit_id).get('message_id'))
        except Exception:
            return False

        return True

    async def _unload_unit(self: "InlineManager", unit_id: str) -> bool:
        """Params `self`, `unit_id` are for internal use only, do not try to pass them"""
        try:
            if "on_unload" in self._units[unit_id] and callable(
                self._units[unit_id]["on_unload"]
            ):
                self._units[unit_id]["on_unload"]()

            if unit_id in self._units:
                del self._units[unit_id]
            else:
                return False
        except Exception:
            return False

        return True

    def build_pagination(
        self: "InlineManager",
        callback: typing.Callable[[int], typing.Awaitable[typing.Any]],
        total_pages: int,
        unit_id: typing.Optional[str] = None,
        current_page: typing.Optional[int] = None,
    ) -> typing.List[typing.List[typing.Dict[str, typing.Any]]]:
        # Based on https://github.com/pystorage/pykeyboard/blob/master/pykeyboard/inline_pagination_keyboard.py#L4
        if current_page is None:
            current_page = self._units[unit_id]["current_index"] + 1

        if total_pages <= 5:
            return [
                [
                    (
                        {"text": number, "args": (number - 1,), "callback": callback}
                        if number != current_page
                        else {
                            "text": f"· {number} ·",
                            "args": (number - 1,),
                            "callback": callback,
                        }
                    )
                    for number in range(1, total_pages + 1)
                ]
            ]

        if current_page <= 3:
            return [
                [
                    (
                        {
                            "text": f"· {number} ·",
                            "args": (number - 1,),
                            "callback": callback,
                        }
                        if number == current_page
                        else (
                            {
                                "text": f"{number} ›",
                                "args": (number - 1,),
                                "callback": callback,
                            }
                            if number == 4
                            else (
                                {
                                    "text": f"{total_pages} »",
                                    "args": (total_pages - 1,),
                                    "callback": callback,
                                }
                                if number == 5
                                else {
                                    "text": number,
                                    "args": (number - 1,),
                                    "callback": callback,
                                }
                            )
                        )
                    )
                    for number in range(1, 6)
                ]
            ]

        if current_page > total_pages - 3:
            return [
                [
                    {"text": "« 1", "args": (0,), "callback": callback},
                    {
                        "text": f"‹ {total_pages - 3}",
                        "args": (total_pages - 4,),
                        "callback": callback,
                    },
                ]
                + [
                    (
                        {
                            "text": f"· {number} ·",
                            "args": (number - 1,),
                            "callback": callback,
                        }
                        if number == current_page
                        else {
                            "text": number,
                            "args": (number - 1,),
                            "callback": callback,
                        }
                    )
                    for number in range(total_pages - 2, total_pages + 1)
                ]
            ]

        return [
            [
                {"text": "« 1", "args": (0,), "callback": callback},
                {
                    "text": f"‹ {current_page - 1}",
                    "args": (current_page - 2,),
                    "callback": callback,
                },
                {
                    "text": f"· {current_page} ·",
                    "args": (current_page - 1,),
                    "callback": callback,
                },
                {
                    "text": f"{current_page + 1} ›",
                    "args": (current_page,),
                    "callback": callback,
                },
                {
                    "text": f"{total_pages} »",
                    "args": (total_pages - 1,),
                    "callback": callback,
                },
            ]
        ]

    def _validate_markup(
        self: "InlineManager",
        buttons: typing.Optional[HerokuReplyMarkup],
    ) -> typing.List[typing.List[typing.Dict[str, typing.Any]]]:
        if buttons is None:
            buttons = []

        if not isinstance(buttons, (list, dict)):
            logger.error(
                "Reply markup ommited because passed type is not valid (%s)",
                type(buttons),
            )
            return None

        buttons = self._normalize_markup(buttons)

        if not all(all(isinstance(button, dict) for button in row) for row in buttons):
            logger.error(
                "Reply markup ommited because passed invalid type for one of the"
                " buttons"
            )
            return None

        if not all(
            all(
                "url" in button
                or "callback" in button
                or "input" in button
                or "data" in button
                or "action" in button
                or "copy" in button
                for button in row
            )
            for row in buttons
        ):
            logger.error(
                "Invalid button specified. "
                "Button must contain one of the following fields:\n"
                "  - `url`\n"
                "  - `callback`\n"
                "  - `input`\n"
                "  - `data`\n"
                "  - `action`"
            )
            return None

        return buttons

    async def _get_webapp_session(self: "InlineManager", url: str):
        session = aiohttp.ClientSession()
        params = unquote(url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
        base_url = url.split("?")[0]

        async with session.post(base_url + f"/api?hash=-", headers=headers, data={"_auth": params, "method": "auth"}) as resp:
            if resp.status != 200:
                logger.error("Error while getting Cookies to enter botfather webapp: resp%s", resp.status)
                await session.close()
                raise RuntimeError("Getting Cookies failed")

        async with session.get(base_url, headers=headers) as resp:
            if resp.status != 200:
                logger.error("Error while getting hash: resp%s", resp.status)
                await session.close()
                raise RuntimeError("Getting hash failed")
            text = await resp.text()
            _hash = HASH_PATTERN.search(text)
            if _hash:
                _hash = _hash.group(1)
            else:
                logger.error("Unexpected error while getting token")
                await session.close()
                raise RuntimeError("No hash provided")

        return (session, _hash)

    async def _main_token_manager(
        self: "InlineManager",
        action: int,
        revoke_token: bool = False,
        create_new_if_needed: bool = True,
        already_initialised: bool = True,
        username: str = ""
    ) -> bool | None:
        url: str = (
            await self._client(RequestWebViewRequest(
                peer="@botfather",
                bot="@botfather",
                platform="android",
                from_bot_menu=False,
                url="https://webappinternal.telegram.org/botfather?")
            )
        ).url
        for _ in range(5):
            await asyncio.sleep(1.5)
            try:
                result = await self._get_webapp_session(url)
            except:
                continue
            break
        else:
            logger.error("WebApp is not available now")
            return False

        session, _hash = result

        main_url = url.split("?")[0]
        try:
            if action == 1:
                return await self._assert_token(
                    session,
                    main_url,
                    _hash,
                    create_new_if_needed=create_new_if_needed,
                    revoke_token=revoke_token
                )
            elif action == 2:
                return await self._create_bot(session, main_url, _hash)
            elif action == 3:
                return await self._dp_revoke_token(
                    session,
                    main_url,
                    _hash,
                    already_initialised=already_initialised
                )
            elif action == 4:
                return await self._reassert_token(session, main_url, _hash)
            elif action == 5:
                return await self._check_bot(
                    session,
                    main_url,
                    _hash,
                    username=username
                )
        finally:
            await session.close()