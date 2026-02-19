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

import git
import time
import git
import psutil
import os
import glob
import requests
import re
import logging
import emoji
import herokutl

from bs4 import BeautifulSoup
from typing import Optional
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from pyrogram.errors import WebpageMediaEmpty
from pyrogram.types import Message, ReplyParameters
from pyrogram.raw.types import InputMediaWebPage
from ..utils import get_display_name
from .. import loader, utils, version
import platform as lib_platform
import getpass

logger = logging.getLogger(__name__)

@loader.tds
class HerokuInfoMod(loader.Module):
    """Show userbot info"""

    strings = {"name": "HerokuInfo"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "custom_message",
                doc=lambda: (
                    "<blockquote expandable>" + self.strings("_cfg_cst_msg") + "\n" + self.strings("_cfg_cst_ph").format(
                        utils.config_placeholders()
                    ) + "</blockquote>"
                )
            ),

            loader.ConfigValue(
                "banner_url",
                "https://raw.githubusercontent.com/coddrago/assets/refs/heads/main/heroku/heroku_info.png",
                lambda: self.strings("_cfg_banner"),
                validator=loader.validators.RandomLink(),
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
            loader.ConfigValue(
                "switchInfo",
                False,
                "Switch info to mode photo",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "imgSettings",
                ["Лапокапканот", 30, '#000', '0|0', "mm", 0, '#000'],
                "Image settings\n1. Дополнительный ник (если прежний ник не отображается)\n2. Размер шрифта\n3. Цвет шрифта в HEX формате '#000'\n4. Координаты текста '100|100', по умолчания в центре фотографии\n5. Якорь текста -> https://pillow.readthedocs.io/en/stable/_images/anchor_horizontal.svg\n6. Размер обводки, по умолчанию 0\n7. Цвет обводки в HEX формате '#000'",
                validator=loader.validators.Series(
                    fixed_len=7,
                ),
            ),
            loader.ConfigValue(
                "quote_media",
                False,
                "Switch preview media to quote",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "invert_media",
                False,
                "Switch preview invert media",
                validator=loader.validators.Boolean(),
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
        
    def remove_emoji_and_html(self, text: str) -> str:
        reg = r'<[^<]+?>'
        text = f"{re.sub(reg, '', text)}"
        allchars = [str for str in text]
        emoji_list = [c for c in allchars if c in emoji.EMOJI_DATA]
        clean_text = ''.join([str for str in text if not any(i in str for i in emoji_list)])
        return clean_text
    
    def imgur(self, url: str) -> str:
        page = requests.get(url, stream=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})
        soup = BeautifulSoup(page.text, 'html.parser')
        metatag = soup.find("meta", property="og:image")
        return metatag['content']

    async def _render_info(self, start: float) -> str:
        try:
            up_to_date = utils.is_up_to_date()
            if up_to_date:
                upd = self.strings["up-to-date"]
            else:
                upd = self.strings["update_required"].format(prefix=self.get_prefix())
        except Exception:
            upd = ""

        me = self.config['imgSettings'][0] if (self.config['imgSettings'][0] != "Лапокапканот") and self.config['switchInfo'] else '<b><a href="tg://user?id={}">{}</a></b>'.format(
            self._client.heroku_me.id,
            utils.escape_html(get_display_name(self._client.heroku_me)),
        ).replace('{', '').replace('}', '')
        build = utils.get_commit_url()
        _version = f'<i>{".".join(list(map(str, list(version.__version__))))}</i>'
        prefix = f"«<code>{utils.escape_html(self.get_prefix())}</code>»"

        platform = utils.get_named_platform()
        platform_emoji = utils.get_named_platform_emoji()

        for emoji, icon in [
            ("🍊", "<tg-emoji emoji-id=\"5449599833973203438\">🧡</tg-emoji>"),
            ("🍇", "<tg-emoji emoji-id=\"5449468596952507859\">💜</tg-emoji>"),
            ("😶‍🌫️", "<tg-emoji emoji-id=\"5370547013815376328\">😶‍🌫️</tg-emoji>"),
            ("❓", "<tg-emoji emoji-id=\"5407025283456835913\">📱</tg-emoji>"),
            ("🍀", "<tg-emoji emoji-id=\"5395325195542078574\">🍀</tg-emoji>"),
            ("🦾", "<tg-emoji emoji-id=\"5386766919154016047\">🦾</tg-emoji>"),
            ("🚂", "<tg-emoji emoji-id=\"5359595190807962128\">🚂</tg-emoji>"),
            ("🐳", "<tg-emoji emoji-id=\"5431815452437257407\">🐳</tg-emoji>"),
            ("🕶", "<tg-emoji emoji-id=\"5407025283456835913\">📱</tg-emoji>"),
            ("🐈‍⬛", "<tg-emoji emoji-id=\"6334750507294262724\">🐈‍⬛</tg-emoji>"),
            ("✌️", "<tg-emoji emoji-id=\"5469986291380657759\">✌️</tg-emoji>"),
            ("💎", "<tg-emoji emoji-id=\"5471952986970267163\">💎</tg-emoji>"),
            ("🛡", "<tg-emoji emoji-id=\"5282731554135615450\">🌩</tg-emoji>"),
            ("🌼", "<tg-emoji emoji-id=\"5224219153077914783\">❤️</tg-emoji>"),
            ("🎡", "<tg-emoji emoji-id=\"5226711870492126219\">🎡</tg-emoji>"),
            ("🐧", "<tg-emoji emoji-id=\"5361541227604878624\">🐧</tg-emoji>"),
            ("🧃", "<tg-emoji emoji-id=\"5422884965593397853\">🧃</tg-emoji>"),
            ("🦅", "<tg-emoji emoji-id=\"5427286516797831670\">🦅</tg-emoji>"),
            ("💻", "<tg-emoji emoji-id=\"5469825590884310445\">💻</tg-emoji>"),
            ("🍏", "<tg-emoji emoji-id=\"5372908412604525258\">🍏</tg-emoji>")
        ]:
            platform_emoji = platform_emoji.replace(emoji, icon)
        data = {
            'me': me,
            'version': _version,
            'build': build,
            'prefix': prefix,
            'platform': platform,
            'platform_emoji': platform_emoji,
            'upd': upd,
            'python_ver': lib_platform.python_version(),
            'uptime': utils.formatted_uptime(),
            'cpu_usage': utils.get_cpu_usage(),
            'ram_usage': f"{utils.get_ram_usage()} MB",
            'branch': version.branch,
            'hostname': lib_platform.node(),
            'user': getpass.getuser(),
            'os': self._get_os_name() or self.strings('non_detectable'),
            'kernel': lib_platform.release(),
            'cpu': f"{psutil.cpu_count(logical=False)} ({psutil.cpu_count()}) core(-s); {psutil.cpu_percent()}% total",
            'ping': round((time.perf_counter_ns() - start) / 10**6, 3),
            'htl_ver': herokutl.__version__,
            'git_status': utils.get_git_status(),
        }
        data = await utils.get_placeholders(data, self.config["custom_message"])
        if self.config["custom_message"]:
            try:
                placeholders_msg = self.config["custom_message"].format(**data)
            except KeyError:
                logger.exception("Missing placeholder in custom_message")
                placeholders_msg = "<tg-emoji emoji-id=5210952531676504517>🚫</tg-emoji>"
        return (
            (
                "🪐 Heroku\n"
                if self.config["show_heroku"]
                else ""
            )
            + placeholders_msg
            if self.config["custom_message"]
            else self.strings["info_message"].format(
                (
                    utils.get_platform_emoji()
                    if self._client.heroku_me.is_premium and self.config["show_heroku"]
                    else ""
                ),
                me = me,
                version = _version,
                prefix = prefix,
                uptime = utils.formatted_uptime(),
                branch = version.branch,
                cpu_usage=utils.get_cpu_usage(),
                ram_usage=f"{utils.get_ram_usage()} MB",
                ping = round((time.perf_counter_ns() - start) / 10**6, 3), 
                upd = upd,
                platform = platform,
                os=self._get_os_name() or self.strings('non_detectable'),
                python_ver = lib_platform.python_version(),
            )
        )
    
    async def _get_info_photo(self, start: float) -> Optional[Path]:
        imgform = str(self.config['banner_url']).split('.')[-1]
        imgset = self.config['imgSettings']
        if imgform in ['jpg', 'jpeg', 'png', 'bmp', 'webp']:
            response = requests.get(str(self.config['banner_url']) if not str(self.config['banner_url']).startswith('https://imgur') else self.imgur(str(self.config['banner_url'])), stream=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})
            img = Image.open(BytesIO(response.content))
            font = ImageFont.truetype(
                glob.glob(f'{os.getcwd()}/assets/font.*')[0], 
                size=int(imgset[1]), 
                encoding='unic'
            )
            w, h = img.size
            draw = ImageDraw.Draw(img)
            draw.text(
                (int(w/2), int(h/2)) if imgset[3] == '0|0' else tuple([int(i) for i in imgset[3].split('|')]),
                f'{utils.remove_html(await self._render_info(start))}', 
                anchor=imgset[4],
                font=font,
                fill=imgset[2] if imgset[2].startswith('#') else '#000',
                stroke_width=int(imgset[5]),
                stroke_fill=imgset[6] if imgset[6].startswith('#') else '#000',
                embedded_color=True
            )
            path = f'{os.getcwd()}/assets/imginfo.{imgform}'
            img.save(path)
            return Path(path).absolute()
        return None
    
    @loader.command()
    async def insfont(self, message: Message):
        "<Url|Reply to font> - Install font"
        match True:
            case _ if message.is_reply:
                reply = message.reply_to_message
                fontform = reply.document.mime_type.split("/")[1]
                if not fontform in ['ttf', 'otf']:
                    await utils.answer(
                        message,
                        self.strings["incorrect_format_font"]
                    )
                    return
                origpath = glob.glob(f'{os.getcwd()}/assets/font.*')[0]
                ptf = f'{os.getcwd()}/font.{fontform}'
                os.rename(origpath, ptf)
                photo = await reply.download_media(origpath)
                if photo is None:
                    os.rename(ptf, origpath)
                    await utils.answer(
                        message,
                        self.strings["no_font"]
                    )
                    return
                os.remove(ptf)
            case _ if utils.check_url(utils.get_args_raw(message)):
                fontform = utils.get_args_raw(message).split('.')[-1]
                if not fontform in ['ttf', 'otf']:
                    await utils.answer(
                        message,
                        self.strings["incorrect_format_font"]
                    )
                    return
                response = requests.get(utils.get_args_raw(message), stream=True)
                os.remove(glob.glob(f'{os.getcwd()}/assets/font.*')[0])
                with open(f'{os.getcwd()}/assets/font.{fontform}', 'wb') as file:
                    file.write(response.content)
            case _:
                await utils.answer(
                    message,
                    self.strings["no_font"]
                )
                return
        await utils.answer(
            message,
            self.strings["font_installed"]
        )

    @loader.command()
    async def infocmd(self, message: Message):
        start = time.perf_counter_ns()
        media = str(self.config["banner_url"])
        
        if self.config["banner_url"] and self.config["quote_media"] is True:
            media = InputMediaWebPage(str(self.config["banner_url"]), optional = True)
        
        elif not self.config["banner_url"]:
            media = None

        try:
            if self.config['switchInfo']:
                if await self._get_info_photo(start) is None:
                    await utils.answer(
                        message, 
                        self.strings["incorrect_img_format"]
                    )
                    return

                await utils.answer(
                    message,
                    "",
                    file = self._get_info_photo(start),
                    reply_parameters=ReplyParameters(message_id=getattr(message, "reply_to_msg_id", None)),
                )
            elif self.config["custom_message"] is None:
                await utils.answer(
                    message,
                    await self._render_info(start),
                    file = media,
                    reply_parameters=ReplyParameters(message_id=getattr(message, "reply_to_msg_id", None)),
                    invert_media = self.config["invert_media"],
                )
            else:
                if '{ping}' in self.config["custom_message"]:
                    message = await utils.answer(message, self.config["ping_emoji"])
                await utils.answer(
                    message,
                    await self._render_info(start),
                    file = media,
                    reply_parameters=ReplyParameters(message_id=getattr(message, "reply_to_msg_id", None)),
                    invert_media = self.config["invert_media"],
                )
        except WebpageMediaEmpty:
            await utils.answer(
                message,
                self.strings["no_banner"].format(
                    link = self.config["banner_url"], 
                ),
                reply_parameters=ReplyParameters(message_id=getattr(message, "reply_to_msg_id", None)),
            )

    @loader.command()
    async def ubinfo(self, message: Message):
        await utils.answer(message, self.strings("desc"))

    @loader.command()
    async def switchinfo(self, message: Message):
        """| switch Image info state"""
        self.config["switchInfo"] = not self.config["switchInfo"]
        if self.config["switchInfo"]:
            await utils.answer(message, self.strings["switchinfo_on"])
        else:
            await utils.answer(message, self.strings["switchinfo_off"])
