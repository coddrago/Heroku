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

import contextlib
import json
import os
import time
from pathlib import Path

import herokutl
from herokutl.extensions.html import CUSTOM_EMOJIS
from herokutl.errors import (
    FloodWaitError,
    PasswordHashInvalidError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    SessionPasswordNeededError,
)
from herokutl.sessions import MemorySession, SQLiteSession
from herokutl.tl.types import Message, User
from herokutl.utils import parse_phone

from .. import loader, main, utils, version
from .._internal import restart
from ..inline.types import InlineCall
from ..tl_cache import CustomTelegramClient


@loader.tds
class CoreMod(loader.Module):
    """Control core userbot settings"""

    strings = {"name": "Settings"}

    def __init__(self):
        self._switch_sessions = {}
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "allow_nonstandart_prefixes",
                False,
                "Allow non-standard prefixes like premium emojis or multi-symbol prefixes",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "alias_emoji",
                "<tg-emoji emoji-id=4974259868996207180>▪️</tg-emoji>",
                "just emoji in .aliases",
            ),
        )

    async def client_ready(self):
        self._markup = utils.chunks(
            [
                {
                    "text": self.strings(platform),
                    "callback": self._inline__choose__installation,
                    "args": (platform,),
                }
                for platform in [
                    "vds",
                    "wsl",
                    "userland",
                    "jamhost",
                    "hikkahost",
                    "lavhost",
                ]
            ],
            2,
        )

    async def blacklistcommon(self, message: Message):
        args = utils.get_args(message)

        if len(args) > 2:
            await utils.answer(message, self.strings("too_many_args"))
            return

        chatid = None
        module = None

        if args:
            try:
                chatid = int(args[0])
            except ValueError:
                module = args[0]

        if len(args) == 2:
            module = args[1]

        if chatid is None:
            chatid = utils.get_chat_id(message)

        module = self.allmodules.get_classname(module)
        return f"{str(chatid)}.{module}" if module else chatid

    @loader.command(
        ru_doc="Информация о Хероку",
        en_doc="Information of Heroku",
        ua_doc="Інформація про Хероку",
        de_doc="Informationen über Heroku",
    )
    async def herokucmd(self, message: Message):
        await utils.answer(
            message,
            self.strings("heroku").format(
                (
                    utils.get_platform_emoji()
                    if self._client.heroku_me.premium and CUSTOM_EMOJIS
                    else "🪐 <b>Heroku userbot</b>"
                ),
                *version.__version__,
                utils.get_commit_url(),
                f"{herokutl.__version__} #{herokutl.tl.alltlobjects.LAYER}",
            )
            + (
                ""
                if version.branch == "master"
                else self.strings("unstable").format(version.branch)
            ),
            file="https://raw.githubusercontent.com/coddrago/assets/refs/heads/main/heroku/heroku_cmd.png",
            reply_to=getattr(message, "reply_to_msg_id", None),
        )

    @loader.command()
    async def blacklist(self, message: Message):
        chatid = await self.blacklistcommon(message)
        chatid_str = str(chatid)

        if chatid_str.startswith("-100"):
            chatid = chatid_str[4:]

        self._db.set(
            main.__name__,
            "blacklist_chats",
            self._db.get(main.__name__, "blacklist_chats", []) + [chatid],
        )

        await utils.answer(message, self.strings("blacklisted").format(chatid))

    @loader.command()
    async def unblacklist(self, message: Message):
        chatid = await self.blacklistcommon(message)
        chatid_str = str(chatid)

        if chatid_str.startswith("-100"):
            chatid = chatid_str[4:]

        self._db.set(
            main.__name__,
            "blacklist_chats",
            list(set(self._db.get(main.__name__, "blacklist_chats", [])) - {chatid}),
        )

        await utils.answer(message, self.strings("unblacklisted").format(chatid))

    async def getuser(self, message: Message):
        try:
            return int(utils.get_args(message)[0])
        except (ValueError, IndexError):
            if reply := await message.get_reply_message():
                return reply.sender_id

            return message.to_id.user_id if message.is_private else False

    @loader.command()
    async def blacklistuser(self, message: Message):
        if not (user := await self.getuser(message)):
            await utils.answer(message, self.strings("who_to_blacklist"))
            return

        self._db.set(
            main.__name__,
            "blacklist_users",
            self._db.get(main.__name__, "blacklist_users", []) + [user],
        )

        await utils.answer(message, self.strings("user_blacklisted").format(user))

    @loader.command()
    async def unblacklistuser(self, message: Message):
        if not (user := await self.getuser(message)):
            await utils.answer(message, self.strings("who_to_unblacklist"))
            return

        self._db.set(
            main.__name__,
            "blacklist_users",
            list(set(self._db.get(main.__name__, "blacklist_users", [])) - {user}),
        )

        await utils.answer(
            message,
            self.strings("user_unblacklisted").format(user),
        )

    @loader.command()
    async def setprefix(self, message: Message):
        if not (args := utils.get_args(message)):
            await utils.answer(message, self.strings("what_prefix"))
            return

        if len(args[0]) != 1 and self.config.get("allow_nonstandart_prefixes") is False:
            await utils.answer(message, self.strings("prefix_incorrect"))
            return

        if args[0] == "s":
            await utils.answer(message, self.strings("prefix_incorrect"))
            return

        if len(args) == 2:
            if args[1].isdigit():
                args[1] = int(args[1])
            try:
                entity = await self.client.get_entity(args[1])
            except:
                return await utils.answer(
                    message, self.strings["invalid_id_or_username"]
                )

            if not isinstance(entity, User):
                return await utils.answer(
                    message, f"The entity {args[1]} is not a User"
                )

            if entity.id != self.tg_id:
                sgroup_users = []
                for g in self._client.dispatcher.security._sgroups.values():
                    for u in g.users:
                        sgroup_users.append(u)

                tsec_users = [
                    rule["target"]
                    for rule in self._client.dispatcher.security._tsec_user
                ]
                ub_owners = self._client.dispatcher.security.owner.copy()

                all_users = sgroup_users + tsec_users + ub_owners

                if entity.id not in all_users:
                    return await utils.answer(
                        message, self.strings["id_not_found_scgroup"]
                    )

                oldprefix = utils.escape_html(self.get_prefix(entity.id))
                all_prefixes = self._db.get(
                    main.__name__,
                    "command_prefixes",
                    {},
                )

                all_prefixes[str(entity.id)] = args[0]

                self._db.set(
                    main.__name__,
                    "command_prefixes",
                    all_prefixes,
                )
                return await utils.answer(
                    message,
                    self.strings("entity_prefix_set").format(
                        "<tg-emoji emoji-id=5197474765387864959>👍</tg-emoji>",
                        entity_name=utils.escape_html(entity.first_name),
                        newprefix=utils.escape_html(args[0]),
                        oldprefix=utils.escape_html(oldprefix),
                        entity_id=args[1],
                    ),
                )

        oldprefix = utils.escape_html(self.get_prefix())

        self._db.set(
            main.__name__,
            "command_prefix",
            args[0],
        )
        await utils.answer(
            message,
            self.strings("prefix_set").format(
                "<tg-emoji emoji-id=5197474765387864959>👍</tg-emoji>",
                newprefix=utils.escape_html(args[0]),
                oldprefix=utils.escape_html(oldprefix),
            ),
        )

    @loader.command()
    async def aliases(self, message: Message):
        await utils.answer(
            message,
            self.strings("aliases")
            + "<blockquote expandable>"
            + "\n".join(
                [
                    (self.config["alias_emoji"] + f" <code>{i}</code> &lt;- {y}")
                    for i, y in self.allmodules.aliases.items()
                ]
            )
            + "</blockquote>",
        )

    @loader.command()
    async def addalias(self, message: Message):

        if len(args := utils.get_args_raw(message).split()) < 2:
            await utils.answer(message, self.strings("alias_args"))
            return

        alias, cmd, *rest = args
        rest = " ".join(rest) if rest else None
        if self.allmodules.add_alias(alias, cmd, rest):
            self.set(
                "aliases",
                {
                    **self.get("aliases", {}),
                    alias: f"{cmd} {rest}" if rest else cmd,
                },
            )
            await utils.answer(
                message,
                self.strings("alias_created").format(utils.escape_html(alias)),
            )
        else:
            await utils.answer(
                message,
                self.strings("no_command").format(utils.escape_html(cmd)),
            )

    @loader.command()
    async def delalias(self, message: Message):
        args = utils.get_args(message)

        if len(args) != 1:
            await utils.answer(message, self.strings("delalias_args"))
            return

        alias = args[0]

        if not self.allmodules.remove_alias(alias):
            await utils.answer(
                message,
                self.strings("no_alias").format(utils.escape_html(alias)),
            )
            return

        current = self.get("aliases", {})
        del current[alias]
        self.set("aliases", current)
        await utils.answer(
            message,
            self.strings("alias_removed").format(utils.escape_html(alias)),
        )

    @loader.command()
    async def cleardb(self, message: Message):
        await self.inline.form(
            self.strings("confirm_cleardb"),
            message,
            reply_markup=[
                {
                    "text": self.strings("cleardb_confirm"),
                    "callback": self._inline__cleardb,
                },
                {
                    "text": self.strings("cancel"),
                    "action": "close",
                },
            ],
        )

    async def _inline__cleardb(self, call: InlineCall):
        self._db.clear()
        self._db.save()
        await utils.answer(call, self.strings("db_cleared"))

    @loader.command()
    async def togglecmdcmd(self, message: Message):
        """Toggle disable specific command of a module: togglecmd <module> <command> or togglecmd <command>"""
        args = utils.get_args(message)
        if not args:
            await utils.answer(message, self.strings("wrong_usage_tcc"))

        if args and len(args) >= 2:
            mod_arg, cmd = args[0], args[1]
            mod_inst = self.allmodules.lookup(mod_arg)
            if not mod_inst:
                await utils.answer(message, self.strings("mod404").format(mod_arg))

        module_key = mod_inst.__class__.__name__

        disabled_commands = self._db.get(main.__name__, "disabled_commands", {})
        current = [x for x in disabled_commands.get(module_key, [])]

        if cmd.lower() not in [c.lower() for c in mod_inst.heroku_commands.keys()]:
            await utils.answer(message, self.strings("cmd404"))

        if any(c.lower() == cmd.lower() for c in current):
            current = [c for c in current if c.lower() != cmd.lower()]
            if current:
                disabled_commands[module_key] = current
            else:
                disabled_commands.pop(module_key, None)

            self._db.set(main.__name__, "disabled_commands", disabled_commands)
            try:
                self.allmodules.register_commands(mod_inst)
            except Exception:
                pass

            await utils.answer(message, f"Command {cmd} enabled in module {module_key}")
        else:
            current.append(cmd)
            disabled_commands[module_key] = current
            self._db.set(main.__name__, "disabled_commands", disabled_commands)

            try:
                self.allmodules.commands.pop(cmd.lower(), None)
            except Exception:
                pass

            for alias, target in list(self.allmodules.aliases.items()):
                if target.split()[0].lower() == cmd.lower():
                    self.allmodules.aliases.pop(alias, None)

            await utils.answer(
                message, f"Command {cmd} disabled in module {module_key}"
            )

    @loader.command()
    async def togglemod(self, message: Message):
        """Toggle disable entire module: togglemod <module>"""
        args = utils.get_args(message)
        if not args:
            await utils.answer(message, self.strings("wrong_usage_tmc"))

        mod_arg = args[0]
        mod_inst = self.allmodules.lookup(mod_arg)
        if not mod_inst:
            await utils.answer(message, self.strings("mod404").format(mod_arg))

        module_key = mod_inst.__class__.__name__
        disabled = self._db.get(main.__name__, "disabled_modules", [])

        if module_key in disabled:
            disabled = [m for m in disabled if m != module_key]
            self._db.set(main.__name__, "disabled_modules", disabled)
            try:
                self.allmodules.register_commands(mod_inst)
                self.allmodules.register_watchers(mod_inst)
                self.allmodules.register_raw_handlers(mod_inst)
                self.allmodules.register_inline_stuff(mod_inst)
            except Exception:
                pass
            await utils.answer(message, self.strings("mod_enabled").format(module_key))
        else:
            disabled += [module_key]
            self._db.set(main.__name__, "disabled_modules", disabled)
            try:
                self.allmodules.unregister_commands(mod_inst, "disable")
                self.allmodules.unregister_watchers(mod_inst, "disable")
                self.allmodules.unregister_raw_handlers(mod_inst, "disable")
                self.allmodules.unregister_inline_stuff(mod_inst, "disable")
            except Exception:
                pass
            await utils.answer(message, self.strings("mod_disabled").format(module_key))

    @loader.command()
    async def clearmodule(self, message: Message):
        """Clear all DB entries for module: clearmodule <module>"""
        args = utils.get_args(message)
        if not args:
            await utils.answer(message, self.strings("wrong_usage_cmc"))

        mod_arg = args[0]
        mod_inst = self.allmodules.lookup(mod_arg)
        if mod_inst:
            module_key = mod_inst.__class__.__name__
        else:
            module_key = mod_arg

        if module_key in self._db:
            try:
                del self._db[module_key]
                self._db.save()
            except Exception:
                pass

        disabled_commands = self._db.get(main.__name__, "disabled_commands", {})
        disabled_commands.pop(module_key, None)
        self._db.set(main.__name__, "disabled_commands", disabled_commands)

        disabled_modules = self._db.get(main.__name__, "disabled_modules", [])
        if module_key in disabled_modules:
            disabled_modules = [m for m in disabled_modules if m != module_key]
            self._db.set(main.__name__, "disabled_modules", disabled_modules)

        await utils.answer(message, f"Cleared DB for module {module_key}")

    async def installationcmd(self, message: Message):
        """| Guide of installation"""

        args = utils.get_args_raw(message)

        if (
            not args or args not in {"-vds", "-wsl", "-ul", "-jh", "-hh", "-lh"}
        ) and not (
            await self.inline.form(
                self.strings("choose_installation"),
                message,
                reply_markup=self._markup,
                photo="https://raw.githubusercontent.com/coddrago/assets/refs/heads/main/heroku/heroku_installation.png",
            )
        ):

            await self.client.send_file(
                message.peer_id,
                "https://raw.githubusercontent.com/coddrago/assets/refs/heads/main/heroku/heroku_installation.png",
                caption=self.strings("vds_install"),
                reply_to=getattr(message, "reply_to_msg_id", None),
            )
        match True:
            case _ if "-vds" in args:
                await utils.answer(message, self.strings("vds_install"))
            case _ if "-wsl" in args:
                await utils.answer(message, self.strings("wsl_install"))
            case _ if "-ul" in args:
                await utils.answer(message, self.strings("userland_install"))
            case _ if "-jh" in args:
                await utils.answer(message, self.strings("jamhost_install"))
            case _ if "-hh" in args:
                await utils.answer(message, self.strings("hikkahost_install"))
            case _ if "-lh" in args:
                await utils.answer(message, self.strings("lavhost_install"))

    async def _inline__choose__installation(self, call: InlineCall, platform: str):
        with contextlib.suppress(Exception):
            await utils.answer(
                call,
                self.strings(f"{platform}_install"),
                reply_markup=self._markup,
            )

    def _switch_owner_key(self, message: Message) -> int:
        return message.sender_id or self.tg_id

    async def _cleanup_switch_state(self, key: int):
        state = self._switch_sessions.pop(key, None)
        if not state:
            return

        client = state.get("client")
        if client:
            with contextlib.suppress(Exception):
                await client.disconnect()

    @staticmethod
    def _dump_json(path: Path, obj: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _clone_db_for_new_account(self, old_id: int, new_id: int):
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

        self._dump_json(new_db_path, old_data)

    @staticmethod
    def _archive_path(path: Path):
        if not path.exists():
            return

        suffix = int(time.time())
        backup = path.with_name(f"{path.name}.bak-{suffix}")
        path.rename(backup)

    def _archive_old_account_files(self, old_id: int):
        base = Path(main.BASE_DIR)
        for name in (
            f"heroku-{old_id}.session",
            f"heroku-{old_id}.session-journal",
            f"config-{old_id}.json",
        ):
            with contextlib.suppress(Exception):
                self._archive_path(base / name)

    @staticmethod
    def _save_session_from_client(client: CustomTelegramClient, telegram_id: int):
        session = SQLiteSession(os.path.join(main.BASE_DIR, f"heroku-{telegram_id}"))
        session.set_dc(
            client.session.dc_id,
            client.session.server_address,
            client.session.port,
        )
        session.auth_key = client.session.auth_key
        session.save()

    def _switch_client(self) -> CustomTelegramClient:
        return CustomTelegramClient(
            MemorySession(),
            main.heroku.api_token.ID,
            main.heroku.api_token.HASH,
            connection=main.heroku.conn,
            proxy=main.heroku.proxy,
            connection_retries=None,
            device_model=main.get_app_name(),
            system_version=main.generate_random_system_version(),
            app_version=".".join(map(str, version.__version__)) + " x64",
            lang_code="en",
            system_lang_code="en-US",
        )

    async def _switch_start_phone(self, call, phone: str, owner_id: int, old_id: int):
        await self._cleanup_switch_state(owner_id)
        client = self._switch_client()
        await client.connect()

        try:
            await client.send_code_request(phone)
        except PhoneNumberInvalidError:
            await client.disconnect()
            await utils.answer(call, self.strings("switch_invalid_phone"))
            return
        except FloodWaitError as e:
            await client.disconnect()
            await utils.answer(
                call,
                self.strings("switch_send_code_failed").format(f"FloodWait({e.seconds})"),
            )
            return
        except Exception as e:
            await client.disconnect()
            await utils.answer(
                call,
                self.strings("switch_send_code_failed").format(type(e).__name__),
            )
            return

        self._switch_sessions[owner_id] = {
            "client": client,
            "phone": phone,
            "old_id": old_id,
        }

        await utils.answer(
            call,
            self.strings("switch_code_sent").format(phone=utils.escape_html(phone)),
            reply_markup={
                "text": self.strings("switch_enter_code_btn"),
                "input": self.strings("switch_enter_code_input"),
                "handler": self._inline_switch_code,
                "args": (owner_id,),
            },
            always_allow=[owner_id],
        )

    async def _switch_finalize(self, call, owner_id: int):
        state = self._switch_sessions.get(owner_id)
        if not state:
            await utils.answer(call, self.strings("switch_no_pending"))
            return

        client = state["client"]
        me = await client.get_me()
        old_id = state.get("old_id", self.tg_id)
        new_id = me.id

        if old_id == new_id:
            await self._cleanup_switch_state(owner_id)
            await utils.answer(call, self.strings("switch_same_account"))
            return

        try:
            self._save_session_from_client(client, new_id)
            self._clone_db_for_new_account(old_id, new_id)
            self._archive_old_account_files(old_id)
        except Exception as e:
            await utils.answer(
                call,
                self.strings("switch_apply_failed").format(type(e).__name__),
            )
            return

        await self._cleanup_switch_state(owner_id)
        await utils.answer(
            call,
            self.strings("switch_applied_restart").format(new_id),
            reply_markup={"text": self.strings("cancel"), "action": "close"},
        )
        restart()

    async def _inline_switch_phone(self, call, data, owner_id: int, old_id: int):
        phone = parse_phone(data)
        if not phone:
            await utils.answer(
                call,
                self.strings("switch_invalid_phone"),
                reply_markup={
                    "text": self.strings("switch_enter_phone_btn"),
                    "input": self.strings("switch_enter_phone_input"),
                    "handler": self._inline_switch_phone,
                    "args": (owner_id, old_id),
                },
                always_allow=[owner_id],
            )
            return

        await self._switch_start_phone(call, phone, owner_id, old_id)

    async def _inline_switch_code(self, call, data, owner_id: int):
        state = self._switch_sessions.get(owner_id)
        if not state:
            await utils.answer(call, self.strings("switch_no_pending"))
            return

        code = "".join(ch for ch in (data or "") if ch.isdigit())
        if len(code) != 5:
            await utils.answer(
                call,
                self.strings("switch_invalid_code"),
                reply_markup={
                    "text": self.strings("switch_enter_code_btn"),
                    "input": self.strings("switch_enter_code_input"),
                    "handler": self._inline_switch_code,
                    "args": (owner_id,),
                },
                always_allow=[owner_id],
            )
            return

        client = state["client"]
        phone = state["phone"]

        try:
            await client.sign_in(phone, code=code)
        except SessionPasswordNeededError:
            await utils.answer(
                call,
                self.strings("switch_need_password"),
                reply_markup={
                    "text": self.strings("switch_enter_password_btn"),
                    "input": self.strings("switch_enter_password_input"),
                    "handler": self._inline_switch_2fa,
                    "args": (owner_id,),
                },
                always_allow=[owner_id],
            )
            return
        except (PhoneCodeInvalidError, PhoneCodeExpiredError):
            await utils.answer(
                call,
                self.strings("switch_invalid_code"),
                reply_markup={
                    "text": self.strings("switch_enter_code_btn"),
                    "input": self.strings("switch_enter_code_input"),
                    "handler": self._inline_switch_code,
                    "args": (owner_id,),
                },
                always_allow=[owner_id],
            )
            return
        except FloodWaitError as e:
            await utils.answer(
                call,
                self.strings("switch_signin_failed").format(f"FloodWait({e.seconds})"),
            )
            return
        except Exception as e:
            await utils.answer(
                call,
                self.strings("switch_signin_failed").format(type(e).__name__),
            )
            return

        await self._switch_finalize(call, owner_id)

    async def _inline_switch_2fa(self, call, data, owner_id: int):
        state = self._switch_sessions.get(owner_id)
        if not state:
            await utils.answer(call, self.strings("switch_no_pending"))
            return

        password = (data or "").strip()
        if not password:
            await utils.answer(
                call,
                self.strings("switch_password_required"),
                reply_markup={
                    "text": self.strings("switch_enter_password_btn"),
                    "input": self.strings("switch_enter_password_input"),
                    "handler": self._inline_switch_2fa,
                    "args": (owner_id,),
                },
                always_allow=[owner_id],
            )
            return

        client = state["client"]
        phone = state["phone"]
        try:
            await client.sign_in(phone, password=password)
        except PasswordHashInvalidError:
            await utils.answer(
                call,
                self.strings("switch_invalid_password"),
                reply_markup={
                    "text": self.strings("switch_enter_password_btn"),
                    "input": self.strings("switch_enter_password_input"),
                    "handler": self._inline_switch_2fa,
                    "args": (owner_id,),
                },
                always_allow=[owner_id],
            )
            return
        except FloodWaitError as e:
            await utils.answer(
                call,
                self.strings("switch_signin_failed").format(f"FloodWait({e.seconds})"),
            )
            return
        except Exception as e:
            await utils.answer(
                call,
                self.strings("switch_signin_failed").format(type(e).__name__),
            )
            return

        await self._switch_finalize(call, owner_id)

    @loader.command(
        ru_doc="[номер] — перенос аккаунта одной командой через inline-ввод кода/2FA",
        en_doc="[phone] — one-command account transfer via inline code/2FA flow",
        ua_doc="[номер] — перенесення акаунта однією командою через inline-ввід коду/2FA",
        de_doc="[nummer] — Ein-Befehl-Kontotransfer über Inline-Code/2FA-Flow",
        jp_doc="[電話番号] — inlineコード/2FAで1コマンド移行",
    )
    async def switchacc(self, message: Message):
        owner_id = self._switch_owner_key(message)
        old_id = self.tg_id
        args = utils.get_args_raw(message)
        phone = parse_phone(args) if args else None

        if phone:
            await self._switch_start_phone(message, phone, owner_id, old_id)
            return

        await utils.answer(
            message,
            self.strings("switch_enter_phone"),
            reply_markup={
                "text": self.strings("switch_enter_phone_btn"),
                "input": self.strings("switch_enter_phone_input"),
                "handler": self._inline_switch_phone,
                "args": (owner_id, old_id),
            },
            always_allow=[owner_id],
        )

    @loader.command(
        ru_doc="отменить незавершенный перенос аккаунта",
        en_doc="cancel pending account transfer",
        ua_doc="скасувати незавершене перенесення акаунта",
        de_doc="ausstehenden Kontotransfer abbrechen",
        jp_doc="保留中のアカウント移行をキャンセル",
    )
    async def switchcancel(self, message: Message):
        key = self._switch_owner_key(message)
        if key not in self._switch_sessions:
            await utils.answer(message, self.strings("switch_no_pending"))
            return

        await self._cleanup_switch_state(key)
        await utils.answer(message, self.strings("switch_cancelled"))
