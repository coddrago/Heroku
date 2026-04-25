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
import logging
import os
import string
import typing

from herokutl.errors import (
    FloodWaitError,
    PasswordHashInvalidError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    SessionPasswordNeededError,
)
from herokutl.sessions import MemorySession, SQLiteSession
from herokutl.tl.custom import Message
from herokutl.tl.types import User
from herokutl.utils import parse_phone

from .. import loader, main, utils
from .._internal import restart
from ..inline.types import InlineCall
from ..tl_cache import CustomTelegramClient
from ..version import __version__
from ..web import core

logger = logging.getLogger(__name__)


@loader.tds
class HerokuWebMod(loader.Module):
    """Web/Inline mode add account"""

    strings = {"name": "HerokuWeb"}

    @loader.command()
    async def weburl(self, message: Message, force: bool = False):

        if "JAMHOST" in os.environ:
            await utils.answer(message, self.strings["host_denied"])
        else:

            if "LAVHOST" in os.environ:
                form = await self.inline.form(
                    self.strings("lavhost_web"),
                    message=message,
                    reply_markup={
                        "text": self.strings("web_btn"),
                        "url": await main.heroku.web.get_url(proxy_pass=False),
                    },
                    photo="https://raw.githubusercontent.com/coddrago/assets/refs/heads/main/heroku/web_interface.png",
                )
                return

            if (
                not force
                and not message.is_private
                and "force_insecure" not in message.raw_text.lower()
            ):
                try:
                    if not await self.inline.form(
                        self.strings("privacy_leak_nowarn").format(self._client.tg_id),
                        message=message,
                        reply_markup=[
                            {
                                "text": self.strings("btn_yes"),
                                "callback": self.weburl,
                                "args": (True,),
                            },
                            {"text": self.strings("btn_no"), "action": "close"},
                        ],
                        photo="https://raw.githubusercontent.com/coddrago/assets/refs/heads/main/heroku/web_interface.png",
                    ):
                        raise Exception
                except Exception:
                    await utils.answer(
                        message,
                        self.strings("privacy_leak").format(
                            self._client.tg_id,
                            utils.escape_html(self.get_prefix()),
                        ),
                    )

                return

            if not main.heroku.web:
                main.heroku.web = core.Web(
                    data_root=main.BASE_DIR,
                    api_token=main.heroku.api_token,
                    proxy=main.heroku.proxy,
                    connection=main.heroku.conn,
                )
                await main.heroku.web.add_loader(
                    self._client, self.allmodules, self._db
                )
                await main.heroku.web.start_if_ready(
                    len(self.allclients),
                    main.heroku.arguments.port,
                    proxy_pass=main.heroku.arguments.proxy_pass,
                )

            if force:
                form = message
                await form.edit(
                    self.strings("opening_tunnel"),
                    reply_markup={"text": "🕔 Wait...", "data": "empty"},
                    photo=(
                        "https://raw.githubusercontent.com/coddrago/assets/refs/heads/main/heroku/opening_tunnel.png"
                    ),
                )
            else:
                form = await self.inline.form(
                    self.strings("opening_tunnel"),
                    message=message,
                    reply_markup={"text": "🕔 Wait...", "data": "empty"},
                    photo=(
                        "https://raw.githubusercontent.com/coddrago/assets/refs/heads/main/heroku/opening_tunnel.png"
                    ),
                )

            url = await main.heroku.web.get_url(proxy_pass=True)

            web_ = main.heroku.web
            if web_._basic_auth and web_._username and web_._password:
                text = self.strings("tunnel_opened_pass").format(
                    web_._username,
                    web_._password,
                )
            else:
                text = self.strings("tunnel_opened")

            await form.edit(
                text,
                reply_markup={"text": self.strings("web_btn"), "url": url},
                photo="https://raw.githubusercontent.com/coddrago/assets/refs/heads/main/heroku/tunnel_opened.png",
            )

    @loader.command()
    async def addacc(self, message: Message):

        if "JAMHOST" in os.environ or "LAVHOST" in os.environ:
            await utils.answer(message, self.strings["host_denied"])
        else:

            id = utils.get_args(message)
            if not id:
                reply = await message.get_reply_message()
                id = reply.sender_id if reply else None
            else:
                id = id[0]

            user = None
            if id:
                try:
                    id = int(id)
                except ValueError:
                    pass

                try:
                    user = await self._client.get_entity(id)
                except Exception as e:
                    logger.error(f"Error while fetching user: {e}")

            if not user or not isinstance(user, User) or user.bot:
                await utils.answer(message, self.strings("invalid_target"))
                return

            if user.id == self.tg_id:
                await self._inline_login(message, user)

            if "force_insecure" in message.text.lower():
                await self._inline_login(message, user)

            try:
                if not await self.inline.form(
                    self.strings("add_user_confirm").format(
                        utils.escape_html(user.first_name),
                        user.id,
                    ),
                    message=message,
                    reply_markup=[
                        {
                            "text": self.strings("btn_yes"),
                            "callback": self._inline_login,
                            "args": (user,),
                        },
                        {"text": self.strings("btn_no"), "action": "close"},
                    ],
                    photo="",
                ):
                    raise Exception
            except Exception:
                await utils.answer(
                    message,
                    self.strings("add_user_insecure").format(
                        utils.escape_html(user.first_name),
                        user.id,
                        utils.escape_html(self.get_prefix()),
                        user.id,
                    ),
                )
            return

    async def _inline_login(
        self,
        call: typing.Union[Message, InlineCall],
        user: User,
        after_fail: bool = False,
        is_switch: bool = False,
    ):
        reply_markup = [
            {
                "text": self.strings("enter_number"),
                "input": self.strings("your_phone_number"),
                "handler": self.inline_phone_handler,
                "args": (user, is_switch),
            }
        ]

        fail = self.strings("incorrect_number") if after_fail else ""

        await utils.answer(
            call,
            fail + self.strings("enter_number_format"),
            reply_markup=reply_markup,
            always_allow=[user.id],
        )

    def _get_client(self) -> CustomTelegramClient:
        return CustomTelegramClient(
            MemorySession(),
            main.heroku.api_token.ID,
            main.heroku.api_token.HASH,
            connection=main.heroku.conn,
            proxy=main.heroku.proxy,
            connection_retries=None,
            device_model=main.get_app_name(),
            system_version="Windows 10",
            app_version=".".join(map(str, __version__)) + " x64",
            lang_code="en",
            system_lang_code="en-US",
        )

    async def schedule_restart(self, call, client, is_switch: bool = False):
        await utils.answer(call, self.strings("login_successful"))
        # Yeah-yeah, ikr, but it's the only way to restart
        await asyncio.sleep(1)
        
        if is_switch:
            old_id = self.tg_id
            new_id = (await client.get_me()).id
            if old_id != new_id:
                import contextlib, json, time
                from pathlib import Path
                
                # Clone DB
                old_db_path = Path(main.BASE_PATH) / f"config-{old_id}.json"
                new_db_path = Path(main.BASE_PATH) / f"config-{new_id}.json"
                if old_db_path.exists():
                    with contextlib.suppress(Exception):
                        old_data = json.loads(old_db_path.read_text(encoding="utf-8"))
                else:
                    old_data = dict(self._db)
                if not isinstance(old_data, dict):
                    old_data = {}
                inline_data = old_data.setdefault("heroku.inline", {})
                if isinstance(inline_data, dict):
                    inline_data["bot_token"] = None
                    inline_data["custom_bot"] = False
                    inline_data.pop("bot_id", None)
                new_db_path.parent.mkdir(parents=True, exist_ok=True)
                new_db_path.write_text(json.dumps(old_data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
                
                # Archive old files
                base = Path(main.BASE_DIR)
                suffix = int(time.time())
                for name in (f"heroku-{old_id}.session", f"heroku-{old_id}.session-journal", f"config-{old_id}.json"):
                    path = base / name
                    if path.exists():
                        with contextlib.suppress(Exception):
                            path.rename(path.with_name(f"{path.name}.bak-{suffix}"))

        await main.heroku.save_client_session(client, delay_restart=False)
        restart()

    async def inline_phone_handler(self, call, data, user, is_switch: bool = False):
        if not (phone := parse_phone(data)):
            await self._inline_login(call, user, after_fail=True, is_switch=is_switch)
            return

        client = self._get_client()

        await client.connect()
        try:
            await client.send_code_request(phone)
        except FloodWaitError as e:
            await utils.answer(
                call,
                self.strings("floodwait_error").format(e.seconds),
                reply_markup={"text": self.strings("btn_no"), "action": "close"},
            )
            return
        except PhoneNumberInvalidError:
            await self._inline_login(call, user, after_fail=True)
            return

        reply_markup = {
            "text": self.strings("enter_code"),
            "input": self.strings("login_code"),
            "handler": self.inline_code_handler,
            "args": (
                client,
                phone,
                user,
                is_switch,
            ),
        }

        await utils.answer(
            call,
            self.strings("code_sent"),
            reply_markup=reply_markup,
            always_allow=[user.id],
        )

    async def inline_code_handler(self, call, data, client, phone, user, is_switch: bool = False):
        _code_markup = {
            "text": self.strings("enter_code"),
            "input": self.strings("login_code"),
            "handler": self.inline_code_handler,
            "args": (
                client,
                phone,
                user,
                is_switch,
            ),
        }
        if not data or len(data) != 5:
            await utils.answer(
                call,
                self.strings("invalid_code"),
                reply_markup=_code_markup,
                always_allow=[user.id],
            )
            return

        if any(c not in string.digits for c in data):
            await utils.answer(
                call,
                "Код должен состоять только из цифр. Повторите попытку.",
                reply_markup=_code_markup,
                always_allow=[user.id],
            )
            return

        try:
            await client.sign_in(phone, code=data)
        except SessionPasswordNeededError:
            reply_markup = [
                {
                    "text": self.strings("enter_2fa"),
                    "input": self.strings("your_2fa"),
                    "handler": self.inline_2fa_handler,
                    "args": (
                        client,
                        phone,
                        user,
                        is_switch,
                    ),
                },
            ]
            await utils.answer(
                call,
                self.strings("2fa_enabled"),
                reply_markup=reply_markup,
                always_allow=[user.id],
            )
            return
        except PhoneCodeExpiredError:
            reply_markup = [
                {
                    "text": self.strings("request_code"),
                    "callback": self.inline_phone_handler,
                    "args": (phone, user),
                }
            ]
            await utils.answer(
                call,
                self.strings("code_expired"),
                reply_markup=reply_markup,
                always_allow=[user.id],
            )
            return
        except PhoneCodeInvalidError:
            await utils.answer(
                call,
                self.strings("invalid_code"),
                reply_markup=_code_markup,
                always_allow=[user.id],
            )
            return
        except FloodWaitError as e:
            await utils.answer(
                call,
                self.strings("floodwait_error").format(e.seconds),
                reply_markup={"text": self.strings("btn_no"), "action": "close"},
            )
            return

        asyncio.ensure_future(self.schedule_restart(call, client, is_switch=is_switch))

    async def inline_2fa_handler(self, call, data, client, phone, user, is_switch: bool = False):
        _2fa_markup = {
            "text": self.strings("enter_2fa"),
            "input": self.strings("your_2fa"),
            "handler": self.inline_2fa_handler,
            "args": (
                client,
                phone,
                user,
                is_switch,
            ),
        }
        if not data:
            await utils.answer(
                call,
                self.strings("invalid_password"),
                reply_markup=_2fa_markup,
                always_allow=[user.id],
            )
            return

        try:
            await client.sign_in(phone, password=data)
        except PasswordHashInvalidError:
            await utils.answer(
                call,
                self.strings("invalid_password"),
                reply_markup=_2fa_markup,
                always_allow=[user.id],
            )
            return
        except FloodWaitError as e:
            await utils.answer(
                call,
                self.strings("floodwait_error").format(e.seconds),
                reply_markup={"text": self.strings("btn_no"), "action": "close"},
            )
            return

        asyncio.ensure_future(self.schedule_restart(call, client, is_switch=is_switch))

    @loader.command(
        ru_doc="<номер> — начать перенос userbot на другой Telegram-аккаунт",
        en_doc="<phone> — start userbot transfer to another Telegram account",
        ua_doc="<номер> — почати перенесення userbot на інший Telegram-акаунт",
        de_doc="<nummer> — Userbot-Transfer auf ein anderes Telegram-Konto starten",
        jp_doc="<電話番号> — 別アカウントへのUserbot移行を開始",
    )
    async def switchacc(self, message: Message):
        user = await self._client.get_entity(self.tg_id)
        if "force_insecure" in message.raw_text.lower():
            await self._inline_login(message, user, is_switch=True)
            return
            
        try:
            if not await self.inline.form(
                self.strings("switch_confirm"),
                message=message,
                reply_markup=[
                    {
                        "text": self.strings("btn_yes"),
                        "callback": self._inline_login,
                        "args": (user, False, True),
                    },
                    {"text": self.strings("btn_no"), "action": "close"},
                ],
                photo="",
            ):
                raise Exception
        except Exception:
            await utils.answer(message, self.strings("switch_insecure").format(self.get_prefix()))
