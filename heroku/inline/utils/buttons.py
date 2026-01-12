# ©️ Codrago, 2024-2030
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import functools
import logging
import typing

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ... import utils
from ..types import HerokuReplyMarkup

if typing.TYPE_CHECKING:
    from ..core import InlineManager

logger = logging.getLogger(__name__)


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

    map_ = _normalize_markup(self, map_)

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

    buttons = _normalize_markup(self, buttons)

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