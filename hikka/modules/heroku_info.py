# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import git
import time

import psutil
from herokutl.tl.types import Message
from herokutl.utils import get_display_name
from .. import loader, utils, version
import platform as lib_platform
import getpass

@loader.tds
class HerokuInfoMod(loader.Module):
    """Show userbot info"""

    strings = {"name": "HerokuInfo"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "custom_message",
                doc=lambda: self.strings("_cfg_cst_msg"),
            ),

            loader.ConfigValue(
                "banner_url",
                "https://imgur.com/a/7LBPJiq.png",
                lambda: self.strings("_cfg_banner"),
            ),

            loader.ConfigValue(
                "show_heroku",
                True,
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "ping_emoji",
                "🪐",
                lambda: self.strings["ping_emoji"],
                validator=loader.validators.String(),
            ),
        )

    def _get_os_name(self):
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME"):
                        return line.split("=")[1].strip().strip('"')
        except FileNotFoundError:
            return self.strings['non_detectable']


    def _render_info(self, inline: bool, start: float) -> str:
        try:
            repo = git.Repo(search_parent_directories=True)
            diff = repo.git.log([f"HEAD..origin/{version.branch}", "--oneline"])
            upd = (
                self.strings("update_required").format(prefix=self.get_prefix()) if diff else self.strings("up-to-date")
            )
        except Exception:
            upd = ""

        me = '<b><a href="tg://user?id={}">{}</a></b>'.format(
            self._client.hikka_me.id,
            utils.escape_html(get_display_name(self._client.hikka_me)),
        ).replace('{', '').replace('}', '')
        build = utils.get_commit_url()
        _version = f'<i>{".".join(list(map(str, list(version.__version__))))}</i>'
        prefix = f"«<code>{utils.escape_html(self.get_prefix())}</code>»"

        platform = utils.get_named_platform()

        for emoji, icon in [
            ("🍊", "<emoji document_id=5449599833973203438>🧡</emoji>"),
            ("🍇", "<emoji document_id=5449468596952507859>💜</emoji>"),
            ("😶‍🌫️", "<emoji document_id=5370547013815376328>😶‍🌫️</emoji>"),
            ("❓", "<emoji document_id=5407025283456835913>📱</emoji>"),
            ("🍀", "<emoji document_id=5395325195542078574>🍀</emoji>"),
            ("🦾", "<emoji document_id=5386766919154016047>🦾</emoji>"),
            ("🚂", "<emoji document_id=5359595190807962128>🚂</emoji>"),
            ("🐳", "<emoji document_id=5431815452437257407>🐳</emoji>"),
            ("🕶", "<emoji document_id=5407025283456835913>📱</emoji>"),
            ("🐈‍⬛", "<emoji document_id=6334750507294262724>🐈‍⬛</emoji>"),
            ("✌️", "<emoji document_id=5469986291380657759>✌️</emoji>"),
            ("💎", "<emoji document_id=5471952986970267163>💎</emoji>"),
            ("🛡", "<emoji document_id=5282731554135615450>🌩</emoji>"),
            ("🌼", "<emoji document_id=5224219153077914783>❤️</emoji>"),
            ("🎡", "<emoji document_id=5226711870492126219>🎡</emoji>"),
            ("🐧", "<emoji document_id=5361541227604878624>🐧</emoji>"),
            ("🧃", "<emoji document_id=5422884965593397853>🧃</emoji>")
        ]:
            platform = platform.replace(emoji, icon)
        return (
            (
                "<b>🪐 Heroku</b>\n"
                if self.config["show_heroku"]
                else ""
            )
            + self.config["custom_message"].format(
                me=me,
                version=_version,
                build=build,
                prefix=prefix,
                platform=platform,
                upd=upd,
                uptime=utils.formatted_uptime(),
                cpu_usage=utils.get_cpu_usage(),
                ram_usage=f"{utils.get_ram_usage()} MB",
                branch=version.branch,
                hostname=lib_platform.node(),
                user=getpass.getuser(),
                os=self._get_os_name() or self.strings('non_detectable'),
                kernel=lib_platform.release(),
                cpu=f"{psutil.cpu_count(logical=False)} ({psutil.cpu_count()}) core(-s); {psutil.cpu_percent()}% total",
                ping=round((time.perf_counter_ns() - start) / 10**6, 3)
            )
            if self.config["custom_message"]
            else (
                f'<b>{{}}</b>\n\n<b>{{}} {self.strings("owner")}:</b> {me}\n\n<b>{{}}'
                f' {self.strings("version")}:</b> {_version} {build}\n<b>{{}}'
                f' {self.strings("branch")}:'
                f"</b> <code>{version.branch}</code>\n{upd}\n\n<b>{{}}"
                f' {self.strings("prefix")}:</b> {prefix}\n<b>{{}}'
                f' {self.strings("uptime")}:'
                f"</b> {utils.formatted_uptime()}\n\n<b>{{}}"
                f' {self.strings("cpu_usage")}:'
                f"</b> <i>~{utils.get_cpu_usage()} %</i>\n<b>{{}}"
                f' {self.strings("ram_usage")}:'
                f"</b> <i>~{utils.get_ram_usage()} MB</i>\n<b>{{}}</b>"
            ).format(
                *map(
                    lambda x: utils.remove_html(x) if inline else x,
                    (
                        (
                            utils.get_platform_emoji()
                            if self._client.hikka_me.premium and self.config["show_heroku"]
                            else ""
                        ),
                        "<emoji document_id=5373141891321699086>😎</emoji>",
                        "<emoji document_id=5469741319330996757>💫</emoji>",
                        "<emoji document_id=5449918202718985124>🌳</emoji>",
                        "<emoji document_id=5472111548572900003>⌨️</emoji>",
                        "<emoji document_id=5451646226975955576>⌛️</emoji>",
                        "<emoji document_id=5431449001532594346>⚡️</emoji>",
                        "<emoji document_id=5359785904535774578>💼</emoji>",
                        platform,
                    ),
                )
            )
        )


    @loader.command()
    async def infocmd(self, message: Message):
        start = time.perf_counter_ns()
        if self.config["custom_message"] is None:
            await utils.answer_file(
                message,
                self.config["banner_url"],
                self._render_info(False, start),
                reply_to=getattr(message, "reply_to_msg_id", None),
            )
        elif '{ping}' in self.config["custom_message"]:
            message = await utils.answer(message, self.config["ping_emoji"])
            await utils.answer_file(
                message,
                self.config["banner_url"],
                self._render_info(False, start),
                reply_to=getattr(message, "reply_to_msg_id", None),
            )
        else:
            await utils.answer_file(
                message,
                self.config["banner_url"],
                self._render_info(False, start),
                reply_to=getattr(message, "reply_to_msg_id", None),
            )

    @loader.command()
    async def herokuinfo(self, message: Message):
        await utils.answer(message, self.strings("desc"))

    @loader.command()
    async def setinfo(self, message: Message):
        if not (args := utils.get_args_html(message)):
            return await utils.answer(message, self.strings("setinfo_no_args"))

        self.config["custom_message"] = args
        await utils.answer(message, self.strings("setinfo_success"))

