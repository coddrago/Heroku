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
import logging
import re
import os
import random
import typing

from .. import utils
from .. import main
from .._internal import fw_protect
from .types import InlineUnit
from . import utils as inutils

if typing.TYPE_CHECKING:
    from ..inline.core import InlineManager

logger = logging.getLogger(__name__)


class TokenObtainment(InlineUnit):
    async def _create_bot(
        self: "InlineManager",
        session: aiohttp.ClientSession,
        url: str,
        _hash: str
    ):
        logger.info("User doesn't have bot, attempting creating new one")

        if self._db.get("heroku.inline", "custom_bot", False):
            username = self._db.get("heroku.inline", "custom_bot").strip("@")
            username = f"@{username}"
            try:
                await self._client.get_entity(username)
            except ValueError:
                pass
            else:
                uid = utils.rand(6)
                genran = "".join(random.choice(main.LATIN_MOCK))
                username = f"@{genran}_{uid}_bot"
        else:
            uid = utils.rand(6)
            genran = "".join(random.choice(main.LATIN_MOCK))
            username = f"@{genran}_{uid}_bot"

        for _ in range(5):
            data = {"username": username, "method": "checkBotUsername"}
            await fw_protect()

            async with session.post(url + f"/api?hash={_hash}", data=data, headers=inutils.headers) as resp:
                if resp.status != 200:
                    logger.error("Error while username check: resp%s", resp.status)
                    return False

                content = await resp.json()
            result = content.get("ok", False)

            if result:
                break

            uid = utils.rand(6)
            genran = "".join(random.choice(main.LATIN_MOCK))
            username = f"@{genran}_{uid}_bot"
        else:
            logger.error("You've got reached limit of tries while checking username")
            return False
        
        try:
            form = aiohttp.FormData()
            form.add_field(
                "file",
                open(f"{os.getcwd()}/assets/heroku.png", "rb"),
                filename="heroku.png",
                content_type="image/png"
            )
            form.add_field(
                "method",
                "uploadMedia"
            )
            form.add_field(
                "target",
                "bot_userpic"
            )
            async with session.post(url + f"/api?hash={_hash}", data=form, headers=inutils.headers) as resp:
                if resp.status != 200:
                    logger.error("Error while uploading bot userpic: resp%s", resp.status)
                    raise RuntimeError("Upload failed")
                content = await resp.json()
                photo_id = content["media"]["photo_id"]
        except (RuntimeError, KeyError):
            photo_id = ""
        
        data = {
            "title": f"🪐 Heroku {utils.get_version_raw()}"[:64],
            "username": username,
            "about": "",
            "userpic": photo_id,
            "method": "createBot"
        }
        await fw_protect()
        async with session.post(url + f"/api?hash={_hash}", data=data, headers=inutils.headers) as resp:
            if resp.status != 200:
                logger.error("Error while creating the bot: resp%s", resp.status)
                return False

            content = await resp.json()
            if not content.get("ok", False):
                logger.error(
                    "Error while creating the bot. "
                    "Maybe you've been banned or exceeded the limit: %s", content)
                return False
            # bot_id = content["bot_id"]

        return await self._assert_token(session, url, _hash, create_new_if_needed=False)

    async def _assert_token(
        self: "InlineManager",
        session: aiohttp.ClientSession,
        url: str,
        _hash: str,
        create_new_if_needed: bool = True,
        revoke_token: bool = False,
    ) -> bool:
        if self._token:
            return True

        logger.info("Bot token not found in db, attempting search in BotFather")

        async with session.get(url, headers=inutils.headers) as resp:
            if resp.status != 200:
                logger.error("Error while getting bot list: resp%s", resp.status)
                return False
            content = await resp.text()

        ids = None
        bot_id = None
            
        username = self._db.get("heroku.inline", "custom_bot", False)
        if username:
            ids = re.search(inutils.BOT_ID_PATTERN.format(username.strip("@")), content)
            
        else:
            ids = inutils.BOT_BASE_PATTERN.search(content)
            
        if ids:
            bot_id = ids.group(1)

        if bot_id:
            if revoke_token:
                async with session.post(
                    url + f"/api?hash={_hash}",
                    data={"bid": bot_id, "method": "revokeAccessToken"},
                    headers=inutils.headers
                ) as resp:
                    if resp.status != 200:
                        logger.error("Error while revoking token: resp%s", resp.status)
                        return False

                    token = (await resp.json())["token"]
            else:
                hdrs = inutils.headers.copy()
                hdrs.update(
                    {
                        "x-aj-referer": "https://webappinternal.telegram.org/botfather",
                        "x-requested-with": "XMLHttpRequest"
                    }
                )
                async with session.get(url + f"/bot/{bot_id}", headers=hdrs) as resp:
                    if resp.status != 200:
                        logger.error("Error while getting token: resp%s", resp.status)
                        return False
                    
                    text = (await resp.json())["h"]
                    token = re.search(r"(\d+:[A-Za-z0-9\-_]{35})", text)
                    token = token.group(1)

            self._db.set("heroku.inline", "bot_token", token)
            self._token = token

            for method, value in {
                "settings[inline]": "true",
                "settings[inph]": "user@heroku:~$",
                "settings[infdb]": "1"
            }.items():
                await fw_protect()

                async with session.post(
                    url + f"/api?hash={_hash}",
                    data={method: value, "bid": bot_id, "method": "changeSettings"},
                    headers=inutils.headers
                ) as resp:
                    if resp.status != 200:
                        logger.error("Error while changing bot inline settings: resp%s", resp.status)
                        return False

            return True

        return await self._create_bot(session, url, _hash) if create_new_if_needed else False

    async def _reassert_token(
        self: "InlineManager",
        session: aiohttp.ClientSession,
        url: str,
        _hash: str
    ):
        is_token_asserted = await self._assert_token(session, url, _hash, revoke_token=True)
        if not is_token_asserted:
            self.init_complete = False
        else:
            await self.register_manager(ignore_token_checks=True)

    async def _dp_revoke_token(
        self: "InlineManager",
        session: aiohttp.ClientSession,
        url: str,
        _hash: str,
        already_initialised: bool = True
    ):
        if already_initialised:
            await self._stop()
            logger.error("Got polling conflict. Attempting token revocation...")

        self._db.set("heroku.inline", "bot_token", None)
        self._token = None
        if already_initialised:
            asyncio.ensure_future(self.reassert_token())
        else:
            return await self._reassert_token(session, url, _hash)
    
    async def _check_bot(
        self: "InlineManager",
        session: aiohttp.ClientSession,
        url: str,
        _hash: str,
        username: str
    ):
        async with session.get(url, headers=inutils.headers) as resp:
            if resp.status != 200:
                logger.error("Error while getting bot list: resp%s", resp.status)
                return False
            content = await resp.text()
        result = re.search(inutils.BOT_ID_PATTERN.format(username), content)

        if not result:
            data = {"username": username, "method": "checkBotUsername"}
            await fw_protect()

            async with session.post(url + f"/api?hash={_hash}", data=data, headers=inutils.headers) as resp:
                if resp.status != 200:
                    logger.error("Error while username check: resp%s", resp.status)
                    return False

                content = await resp.json()
            result = content.get("ok", False)
        return result

    async def assert_token(
        self: "InlineManager",
        create_new_if_needed: bool = True,
        revoke_token: bool = False
    ):
        return await self._main_token_manager(
            1,
            create_new_if_needed=create_new_if_needed,
            revoke_token=revoke_token
        )
        
    async def create_bot(self: "InlineManager"):
        return await self._main_token_manager(2)

    async def dp_revoke_token(self: "InlineManager", already_initialised: bool = True):
        return await self._main_token_manager(3, already_initialised=already_initialised)

    async def reassert_token(self: "InlineManager"):
        return await self._main_token_manager(4)
    
    async def check_bot(self: "InlineManager", username: str):
        return await self._main_token_manager(5, username=username)