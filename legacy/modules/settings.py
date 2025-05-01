# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

from legacytl.extensions.html import CUSTOM_EMOJIS
from legacytl.tl.types import Message

from .. import loader, main, utils
from ..inline.types import InlineCall


@loader.tds
class CoreMod(loader.Module):
    """Control core userbot settings"""

    strings = {"name": "Settings"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "allow_nonstandart_prefixes",
                False,
                "Allow non-standard prefixes like premium emojis or multi-symbol prefixes",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "alias_emoji",
                "<emoji document_id=4974259868996207180>▪️</emoji>",
                "just emoji in .aliases",
            ),
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

    @loader.command(ru_doc="Информация о Legacy", en_doc="Information of Legacy", ua_doc="Інформація про Хероку", de_doc="Informationen über Legacy")
    async def legacy(self, message: Message):
        await utils.answer_file(
            message,
            "https://i.postimg.cc/VsxbMHnP/41-368214-A.gif",
            self.strings("legacy").format(
                (
                    utils.get_platform_emoji()
                    if self._client.legacy_me.premium and CUSTOM_EMOJIS
                    else "🌙 <b>Legacy userbot</b>"
                ),
            )
        )

    @loader.command()
    async def blacklist(self, message: Message):
        chatid = await self.blacklistcommon(message)

        self._db.set(
            main.__name__,
            "blacklist_chats",
            self._db.get(main.__name__, "blacklist_chats", []) + [chatid],
        )

        await utils.answer(message, self.strings("blacklisted").format(chatid))

    @loader.command()
    async def unblacklist(self, message: Message):
        chatid = await self.blacklistcommon(message)

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
        if not (args := utils.get_args_raw(message)):
            await utils.answer(message, self.strings("what_prefix"))
            return

        if len(args) != 1 and self.config.get("allow_nonstandart_prefixes") is False:
            await utils.answer(message, self.strings("prefix_incorrect"))
            return

        if args == "s":
            await utils.answer(message, self.strings("prefix_incorrect"))
            return

        oldprefix = utils.escape_html(self.get_prefix())

        self._db.set(
            main.__name__,
            "command_prefix",
            args,
        )
        await utils.answer(
            message,
            self.strings("prefix_set").format(
                "<emoji document_id=5197474765387864959>👍</emoji>",
                newprefix=utils.escape_html(args),
                oldprefix=utils.escape_html(oldprefix),
            ),
        )

    @loader.command()
    async def aliases(self, message: Message):
        await utils.answer(
            message,
            self.strings("aliases")
            + "\n".join(
                [
                    (self.config["alias_emoji"] + f" <code>{i}</code> &lt;- {y}")
                    for i, y in self.allmodules.aliases.items()
                ]
            ),
        )

    @loader.command()
    async def addalias(self, message: Message):
        if len(args := utils.get_args(message)) != 2:
            await utils.answer(message, self.strings("alias_args"))
            return

        alias, cmd = args
        if self.allmodules.add_alias(alias.lower(), cmd):
            self.set(
                "aliases",
                {
                    **self.get("aliases", {}),
                    alias: cmd,
                },
            )
            await utils.answer(
                message,
                self.strings("alias_created").format(utils.escape_html(alias.lower())),
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
        current.pop(alias, None)
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

    async def _main_installation(self, call: InlineCall):
        reply_markup = [
            [{"text": self.strings("vds"), "callback": self._vds_installation}, {"text": self.strings("termux"), "callback": self._termux_installation}],
            [{"text": self.strings("railway"), "callback": self._railway_installation}],
            [{"text": self.strings("close_btn"), "action": "close"}]
        ]
        await utils.answer(call, self.strings("choose_installation"), reply_markup=reply_markup)

    async def _termux_installation(self, call: InlineCall):
        reply_markup = [
            [{
                "text": self.strings("main_menu"), "callback": self._main_installation
            }]
        ]
        await utils.answer(call, self.strings("termux_install"), reply_markup=reply_markup)

    async def _vds_installation(self, call: InlineCall):
        reply_markup = [
            [{
                "text": self.strings("main_menu"), "callback": self._main_installation
            }]
        ]
        await utils.answer(call, self.strings("vds_install"), reply_markup=reply_markup)

    async def _railway_installation(self, call: InlineCall):
        reply_markup = [
            [{
                "text": self.strings("main_menu"), "callback": self._main_installation
            }]
        ]
        await utils.answer(call, self.strings("railway_install"), reply_markup=reply_markup)

    @loader.command()
    async def installation(self, message: Message):
        """| Guide of installation"""
        args = utils.get_args(message)
        if "-t" in args or "--termux" in args:
            return await utils.answer(message, self.strings("termux_install"))
        elif "-v" in args or "--vds" in args:
            return await utils.answer(message, self.strings("vds_install"))
        elif "-r" in args or "--railway" in args:
            return await utils.answer(message, self.strings("railway_install"))
        else:
            reply_markup = [
                [{"text": self.strings("vds"), "callback": self._vds_installation}, {"text": self.strings("termux"), "callback": self._termux_installation}],
                [{"text": self.strings("railway"), "callback": self._railway_installation}],
                [{"text": self.strings("close_btn"), "action": "close"}]
            ]
            await message.delete()
            await self.inline.form(
                message=message,
                text=self.strings("choose_installation"),
                reply_markup=reply_markup,
                **(
                    {"photo": "https://i.postimg.cc/NfKrrv54/41-2807-ED0.gif"}
                ),
            )
