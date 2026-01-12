# ©️ Codrago, 2024-2030
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import contextlib
import functools
import itertools
import logging
import typing

from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from .. import utils
from ..types import InlineCall, InlineUnit, HerokuReplyMarkup

if typing.TYPE_CHECKING:
    from ..core import InlineManager

logger = logging.getLogger(__name__)


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


class Utils(InlineUnit):
    def _generate_markup(
        self,
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
                    match True:
                        case _ if "url" in button:
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

                        case _ if "callback" in button:
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

                        case _ if "input" in button:
                            line += [
                                InlineKeyboardButton(
                                    text=str(button["text"]),
                                    switch_inline_query_current_chat=button["_switch_query"]
                                    + " ",
                                )
                            ]

                        case _ if "data" in button:
                            line += [
                                InlineKeyboardButton(
                                    text=str(button["text"]),
                                    callback_data=button["data"],
                                )
                            ]

                        case _ if "web_app" in button:
                            from aiogram.types import WebAppInfo
                            line += [
                                InlineKeyboardButton(
                                    text=str(button["text"]),
                                    web_app=WebAppInfo(button["data"]),
                                )
                            ]

                        case _ if "copy" in button:
                            from aiogram.types import CopyTextButton
                            line += [
                                InlineKeyboardButton(
                                    text=str(button["text"]),
                                    copy_text=CopyTextButton(
                                        text=button["copy"]
                                    )
                                )
                            ]

                        case _ if "switch_inline_query_current_chat" in button:
                            line += [
                                InlineKeyboardButton(
                                    text=str(button["text"]),
                                    switch_inline_query_current_chat=button[
                                        "switch_inline_query_current_chat"
                                    ],
                                )
                            ]

                        case _ if "switch_inline_query" in button:
                            line += [
                                InlineKeyboardButton(
                                    text=str(button["text"]),
                                    switch_inline_query_current_chat=button[
                                        "switch_inline_query"
                                    ],
                                )
                            ]

                        case _:
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

    def _normalize_markup(
        self, reply_markup: HerokuReplyMarkup
    ) -> typing.List[typing.List[typing.Dict[str, typing.Any]]]:
        if isinstance(reply_markup, dict):
            return [[reply_markup]]

        if isinstance(reply_markup, list) and any(
            isinstance(i, dict) for i in reply_markup
        ):
            return [reply_markup]

        return reply_markup

    def _validate_markup(
        self,
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
    
    async def _main_token_manager(self, op: int, **kwargs):
        """Main token manager dispatcher"""
        import aiohttp
        from . import utils as inutils

        url = "https://webappinternal.telegram.org/botfather"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=inutils.headers) as resp:
                if resp.status != 200:
                    logger.error("Error while getting botfather page: resp%s", resp.status)
                    return False
                content = await resp.text()

            _hash_match = inutils.HASH_PATTERN.search(content)
            if not _hash_match:
                logger.error("Could not find hash in botfather page")
                return False
            _hash = _hash_match.group(1)

            if op == 1:  # assert_token
                return await self._assert_token(session, url, _hash, **kwargs)
            elif op == 2:  # create_bot
                return await self._create_bot(session, url, _hash)
            elif op == 3:  # dp_revoke_token
                return await self._dp_revoke_token(session, url, _hash, **kwargs)
            elif op == 4:  # reassert_token
                return await self._reassert_token(session, url, _hash)
            elif op == 5:  # check_bot
                return await self._check_bot(session, url, _hash, **kwargs)
            else:
                raise ValueError(f"Unknown operation {op}")