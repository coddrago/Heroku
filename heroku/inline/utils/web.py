# ©️ Codrago, 2024-2030
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import aiohttp
import logging
import re
import typing
from urllib.parse import unquote

from herokutl.tl.functions.messages import RequestWebViewRequest

if typing.TYPE_CHECKING:
    from ..core import InlineManager

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
            result = await _get_webapp_session(self, url)
        except:
            continue
        break
    else:
        logger.error("WebApp is not available now")
        return False

    session, _hash = result

    main_url = url.split("?")[0]
    try:
        match action:
            case 1:
                return await self._assert_token(
                    session,
                    main_url,
                    _hash,
                    create_new_if_needed=create_new_if_needed,
                    revoke_token=revoke_token,
                )
            case 2:
                return await self._create_bot(session, main_url, _hash)
            case 3:
                return await self._dp_revoke_token(
                    session,
                    main_url,
                    _hash,
                    already_initialised=already_initialised,
                )
            case 4:
                return await self._reassert_token(session, main_url, _hash)
            case 5:
                return await self._check_bot(
                    session,
                    main_url,
                    _hash,
                    username=username,
                )
    finally:
        await session.close()