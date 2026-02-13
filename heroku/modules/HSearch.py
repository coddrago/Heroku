__version__ = (2, 0, 0)
# meta developer: @FModules

# ©️ Fixyres, 2024-2030
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
import aiohttp
import ast
import sys
import uuid
from typing import Optional, Dict, List
from urllib.parse import unquote
from importlib.machinery import ModuleSpec

from .. import loader, utils
from ..types import CoreOverwriteError
from herokutl.tl.functions.contacts import UnblockRequest
from herokutl.errors.common import ScamDetectionError


@loader.tds
class HSearch(loader.Module):
    '''Module for searching modules! Watch all HSearch news in @FHeta_Updates!'''

    strings = {
        "name": "HSearch"
    }
    
    THEMES = {
        "default": {
            "search": '<tg-emoji emoji-id="5188217332748527444">🔍</tg-emoji>',
            "error": '<tg-emoji emoji-id="5465665476971471368">❌</tg-emoji>',
            "warn": '<tg-emoji emoji-id="5447644880824181073">⚠️</tg-emoji>',
            "description": '<tg-emoji emoji-id="5334882760735598374">📝</tg-emoji>',
            "command": '<tg-emoji emoji-id="5341715473882955310">⚙️</tg-emoji>',
            "like": "👍",
            "dislike": "👎",
            "prev": "◀️",
            "next": "▶️",
            "module": '<tg-emoji emoji-id="5454112830989025752">📦</tg-emoji>',
            "close": "❌",
            "removed": "🗑️",
            "modules_list": '<tg-emoji emoji-id="5197269100878907942">📋</tg-emoji>',
            "notify_success": "✅",
            "notify_error": "❌",
            "notify_overwrite": "⚠️",
            "notify_requirements": "❌"
        },
        "winter": {
            "search": '<tg-emoji emoji-id="5431895003821513760">❄️</tg-emoji>',
            "error": '<tg-emoji emoji-id="5404728536810398694">🧊</tg-emoji>',
            "warn": '<tg-emoji emoji-id="5447644880824181073">🌨️</tg-emoji>',
            "description": '<tg-emoji emoji-id="5255850496291259327">📜</tg-emoji>',
            "command": '<tg-emoji emoji-id="5199503707938505333">🎅</tg-emoji>',
            "like": "☕",
            "dislike": "🥶",
            "prev": "⏮️",
            "next": "⏭️",
            "module": '<tg-emoji emoji-id="5197708768091061888">🎁</tg-emoji>',
            "close": "❌",
            "removed": "🗑️",
            "modules_list": '<tg-emoji emoji-id="5345935030143196497">🎄</tg-emoji>',
            "notify_success": "🎁",
            "notify_error": "🧊",
            "notify_overwrite": "🌨️",
            "notify_requirements": "🧊"
        },
        "summer": {
            "search": '<tg-emoji emoji-id="5188217332748527444">🔍</tg-emoji>',
            "error": '<tg-emoji emoji-id="5470049770997292425">🌡️</tg-emoji>',
            "warn": '<tg-emoji emoji-id="5447644880824181073">⚠️</tg-emoji>',
            "description": '<tg-emoji emoji-id="5361684086807076580">🍹</tg-emoji>',
            "command": '<tg-emoji emoji-id="5442644589703866634">🏄</tg-emoji>',
            "like": "🍓",
            "dislike": "🥵",
            "prev": "⬅️",
            "next": "➡️",
            "module": '<tg-emoji emoji-id="5433645645376264953">🏖️</tg-emoji>',
            "close": "❌",
            "removed": "🗑️",
            "modules_list": '<tg-emoji emoji-id="5472178859300363509">🏖️</tg-emoji>',
            "notify_success": "🍹",
            "notify_error": "🌡️",
            "notify_overwrite": "🥵",
            "notify_requirements": "🌡️"
        },
        "spring": {
            "search": '<tg-emoji emoji-id="5449885771420934013">🌱</tg-emoji>',
            "error": '<tg-emoji emoji-id="5208923808169222461">🥀</tg-emoji>',
            "warn": '<tg-emoji emoji-id="5447644880824181073">⚠️</tg-emoji>',
            "description": '<tg-emoji emoji-id="5251524493561569780">🍃</tg-emoji>',
            "command": '<tg-emoji emoji-id="5449850741667668411">🦋</tg-emoji>',
            "like": "🌸",
            "dislike": "🌧️",
            "prev": "⏪",
            "next": "⏩",
            "module": '<tg-emoji emoji-id="5440911110838425969">🌿</tg-emoji>',
            "close": "❌",
            "removed": "🗑️",
            "modules_list": '<tg-emoji emoji-id="5440748683765227563">🌺</tg-emoji>',
            "notify_success": "🌺",
            "notify_error": "🥀",
            "notify_overwrite": "🌧️",
            "notify_requirements": "🥀"
        },
        "autumn": {
            "search": '<tg-emoji emoji-id="5253944419870062295">🍂</tg-emoji>',
            "error": '<tg-emoji emoji-id="5281026503658728615">🍁</tg-emoji>',
            "warn": '<tg-emoji emoji-id="5447644880824181073">⚠️</tg-emoji>',
            "description": '<tg-emoji emoji-id="5406631276042002796">📜</tg-emoji>',
            "command": '<tg-emoji emoji-id="5212963577098417551">🍂</tg-emoji>',
            "like": "🍎",
            "dislike": "🌧️",
            "prev": "👈",
            "next": "👉",
            "module": '<tg-emoji emoji-id="5249157915041865558">🍄</tg-emoji>',
            "close": "❌",
            "removed": "🗑️",
            "modules_list": '<tg-emoji emoji-id="5305495722618010655">🍂</tg-emoji>',
            "notify_success": "🍄",
            "notify_error": "🍁",
            "notify_overwrite": "🌧️",
            "notify_requirements": "🍁"
        }
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "theme",
                "default",
                lambda: self.strings("_cfg_doc_theme"),
                validator=loader.validators.Choice(["default", "winter", "summer", "spring", "autumn"])
            )
        )

    async def client_ready(self, client, db):
        try:
            await client(UnblockRequest("@FHeta_robot"))
            await utils.dnd(client, "@FHeta_robot", archive=True)
        except:
            pass
            
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
            
        self.token = db.get("HSearch", "token")
        asyncio.create_task(self._sync_loop())

    async def _sync_loop(self):
        ll = None

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            while True:
                try:
                    cl = self.strings["lang"]
                    if cl != ll:
                        async with session.post(
                            "https://api.fixyres.com/dataset",
                            params={
                                "user_id": self.uid,
                                "lang": cl
                            },
                            headers={"Authorization": self.token}
                        ) as response:
                            await response.release()
                        ll = cl
                except:
                    pass

                await asyncio.sleep(60)

    async def _api_get(self, endpoint: str, **params):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.fixyres.com/{endpoint}",
                    params=params,
                    headers={"Authorization": self.token},
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
                    timeout=aiohttp.ClientTimeout(total=180)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return {}
        except:
            return {}

    def _get_emoji(self, key: str) -> str:
        return self.THEMES[self.config["theme"]][key]

    def _fmt_mod(self, mod: Dict, query: str = "", idx: int = 1, total: int = 1, inline: bool = False) -> str:
        version = mod.get("version", "?.?.?")
        
        if version and version != "?.?.?":
            info = self.strings["module_info_version"].format(
                emoji=self._get_emoji("module"),
                name=utils.escape_html(mod.get("name", "")),
                author=utils.escape_html(mod.get("author", "???")),
                version=utils.escape_html(version)
            )
        else:
            info = self.strings["module_info"].format(
                emoji=self._get_emoji("module"),
                name=utils.escape_html(mod.get("name", "")),
                author=utils.escape_html(mod.get("author", "???"))
            )

        desc = mod.get("description")
        if desc:
            if isinstance(desc, dict):
                text = desc.get(self.strings["lang"]) or desc.get("doc") or next(iter(desc.values()), "")
            else:
                text = desc
            
            info += self.strings["desc"].format(desc=utils.escape_html(text), emoji=self._get_emoji("description"))

        info += self._fmt_cmds(mod.get("commands", []), limit=3700 - len(info))
        return info

    def _fmt_cmds(self, cmds: List[Dict], limit: int) -> str:
        cmd_lines = []
        lang = self.strings["lang"]
        
        for cmd in cmds:
            desc_dict = cmd.get("description", {})
            desc_text = desc_dict.get(lang) or desc_dict.get("doc") or ""
            
            if isinstance(desc_text, dict):
                desc_text = desc_text.get("doc", "")
            
            cmd_name = utils.escape_html(cmd.get("name", ""))
            cmd_desc = utils.escape_html(desc_text) if desc_text else ""

            if cmd.get("inline"):
                line = f"<code>@{self.inline.bot_username} {cmd_name}</code> {cmd_desc}"
            else:
                line = f"<code>{self.get_prefix()}{cmd_name}</code> {cmd_desc}"
            
            current_text = "\n".join(cmd_lines)
            test_text = current_text + ("\n" if current_text else "") + line
            
            if len(test_text) > limit:
                break
            
            cmd_lines.append(line)

        if cmd_lines:
            return self.strings["cmds"].format(cmds="\n".join(cmd_lines), emoji=self._get_emoji("command"))
            
        return ""

    def _mk_btns(self, install: str, stats: Dict, idx: int, mods: Optional[List] = None, query: str = "") -> List[List[Dict]]:
        like_emoji = self._get_emoji("like")
        dislike_emoji = self._get_emoji("dislike")
        prev_emoji = self._get_emoji("prev")
        next_emoji = self._get_emoji("next")
        
        buttons = []
        
        decoded_install = unquote(install.replace('%20', '___SPACE___')).replace('___SPACE___', '%20')
        install_url = decoded_install[4:] if decoded_install.startswith('dlm ') else decoded_install
        
        if query:
            buttons.append([
                {"text": self.strings["query_label"], "copy": query},
                {"text": self.strings["install_btn"], "callback": self._install_cb, "args": (install_url, idx, mods, query)},
                {"text": "URL", "copy": install_url}
            ])
        
        buttons.append([
            {"text": f"{like_emoji} {stats.get('likes', 0)}", "callback": self._rate_cb, "args": (install, "like", idx, mods, query)},
            {"text": f"{dislike_emoji} {stats.get('dislikes', 0)}", "callback": self._rate_cb, "args": (install, "dislike", idx, mods, query)}
        ])
        
        if mods and len(mods) > 1:
            buttons[-1].insert(1, {"text": self.strings["results_count"].format(idx=idx+1, total=len(mods)), "callback": self._show_list_cb, "args": (idx, mods, query)})

        if mods and len(mods) > 1:
            nav_buttons = []
            if idx > 0:
                nav_buttons.append({"text": prev_emoji, "callback": self._nav_cb, "args": (idx - 1, mods, query)})
            if idx < len(mods) - 1:
                nav_buttons.append({"text": next_emoji, "callback": self._nav_cb, "args": (idx + 1, mods, query)})
            if nav_buttons:
                buttons.append(nav_buttons)

        return buttons

    def _mk_list_btns(self, mods: List, query: str, page: int = 0, current_idx: int = 0) -> List[List[Dict]]:
        prev_emoji = self._get_emoji("prev")
        next_emoji = self._get_emoji("next")
        close_emoji = self._get_emoji("close")
        
        buttons = []
        items_per_page = 8
        total_pages = (len(mods) + items_per_page - 1) // items_per_page
        
        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, len(mods))
        
        for i in range(start_idx, end_idx):
            mod = mods[i]
            name = mod.get("name", "Unknown")
            author = mod.get("author", "???")
            button_text = f"{i + 1}. {name} by {author}"
            buttons.append([
                {"text": button_text, "callback": self._select_from_list_cb, "args": (i, mods, query)}
            ])
        
        nav_buttons = []
        if page > 0:
            nav_buttons.append({"text": prev_emoji, "callback": self._list_page_cb, "args": (page - 1, mods, query, current_idx)})
        if page < total_pages - 1:
            nav_buttons.append({"text": next_emoji, "callback": self._list_page_cb, "args": (page + 1, mods, query, current_idx)})
        
        if nav_buttons:
            buttons.append(nav_buttons)
        
        buttons.append([
            {"text": close_emoji, "callback": self._close_list_cb, "args": (current_idx, mods, query)}
        ])
        
        return buttons

    async def _list_page_cb(self, call, page: int, mods: List, query: str, current_idx: int):
        try:
            await call.edit(
                text=self.strings["modules_list"].format(emoji=self._get_emoji("modules_list")),
                reply_markup=self._mk_list_btns(mods, query, page, current_idx)
            )
        except:
            pass

    async def _select_from_list_cb(self, call, idx: int, mods: List, query: str):
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

    async def _close_list_cb(self, call, idx: int, mods: List, query: str):
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
                    await call.answer(self.strings["rating_removed"].format(emoji=self._get_emoji("removed")), show_alert=True)
            except:
                pass

    async def _install_cb(self, call, install_url: str, idx: int, mods: Optional[List], query: str = ""):
        lm = self.lookup("loader")
        
        try:
            r = await lm._storage.fetch(install_url, auth=lm.config.get("basic_auth"))
        except (aiohttp.ClientError, aiohttp.ClientResponseError) as e:
            try:
                await call.answer(
                    self.strings["error"].format(emoji=self._get_emoji("notify_error")),
                    show_alert=True
                )
            except:
                pass
            return
        
        doc = r
        origin = install_url
        
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                result = await self._load_module(lm, doc, origin, attempt)
                
                if result == "success":
                    if lm.fully_loaded:
                        lm.update_modules_in_db()
                    
                    try:
                        await call.answer(
                            self.strings["success"].format(emoji=self._get_emoji("notify_success")),
                            show_alert=False
                        )
                    except:
                        pass
                    return
                
                elif result == "retry":
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(0.33)
                        continue
                    else:
                        try:
                            await call.answer(
                                self.strings["requirements"].format(emoji=self._get_emoji("notify_requirements")),
                                show_alert=True
                            )
                        except Exception:
                            pass
                        return
                
                elif isinstance(result, dict) and result.get("type") == "requirements_error":
                    deps = result.get("deps", [])
                    if deps:
                        deps_text = ", ".join(deps[:5])
                        try:
                            await call.answer(
                                self.strings["requirements_deps"].format(
                                    emoji=self._get_emoji("notify_requirements"),
                                    deps=deps_text
                                ),
                                show_alert=True
                            )
                        except:
                            pass
                    else:
                        try:
                            await call.answer(
                                self.strings["requirements"].format(emoji=self._get_emoji("notify_requirements")),
                                show_alert=True
                            )
                        except:
                            pass
                    return
                
                elif result == "overwrite":
                    try:
                        await call.answer(
                            self.strings["overwrite"].format(emoji=self._get_emoji("notify_overwrite")),
                            show_alert=True
                        )
                    except:
                        pass
                    return
                
                else:
                    try:
                        await call.answer(
                            self.strings["error"].format(emoji=self._get_emoji("notify_error")),
                            show_alert=True
                        )
                    except:
                        pass
                    return
                    
            except:
                try:
                    await call.answer(
                        self.strings["error"].format(emoji=self._get_emoji("notify_error")),
                        show_alert=True
                    )
                except:
                    pass
                return
        
        try:
            await call.answer(
                self.strings["requirements"].format(emoji=self._get_emoji("notify_requirements")),
                show_alert=True
            )
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

    @loader.inline_handler()
    async def hs(self, query):
        '''(query) - search modules.'''
        if not query.args:
            return {
                "title": self.strings["inline_no_query"],
                "description": self.strings["inline_desc"],
                "message": self.strings["inline_no_query"].format(emoji=self._get_emoji("error")),
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
                "message": self.strings["inline_no_results"].format(emoji=self._get_emoji("error")),
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
                "thumb": mod.get("pic") or "https://raw.githubusercontent.com/Fixyres/FHeta/refs/heads/main/assets/empty_pic.png",
                "message": self._fmt_mod(mod, query.args, inline=True),
                "reply_markup": self._mk_btns(mod.get("install", ""), stats, 0, None, query.args),
            })

        return results

    @loader.command()
    async def hscmd(self, message):
        '''(query) - search modules.'''
        query = utils.get_args_raw(message)
        
        if not query:
            await utils.answer(message, self.strings["no_query"].format(emoji=self._get_emoji("error"), prefix=self.get_prefix()))
            return

        if len(query) > 168:
            await utils.answer(message, self.strings["query_too_big"].format(emoji=self._get_emoji("warn")))
            return

        status_msg = await utils.answer(message, self.strings["searching"].format(emoji=self._get_emoji("search"), query=utils.escape_html(query)))
        mods = await self._api_get("search", query=query, inline="false", token=self.token, user_id=self.uid, ood="true")

        if not mods or not isinstance(mods, list):
            await utils.answer(message, self.strings["no_results"].format(emoji=self._get_emoji("error"), query=utils.escape_html(query)))
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
        
        if self.lookup("FHeta"):
            return
        
        try:
            parsed_url = urlparse(link)
            qp = parse_qs(parsed_url.query)
            
            ohd = qp.get('ohd', ['False'])[0]
            
            if ohd.lower() == 'false':
                warn_msg = await message.respond("⚠️")
                await asyncio.sleep(1)
                await warn_msg.delete()
                await message.delete()
                return

            lm = self.lookup("loader")
            
            try:
                r = await lm._storage.fetch(link, auth=lm.config.get("basic_auth"))
            except (aiohttp.ClientError, aiohttp.ClientResponseError):
                status_msg = await message.respond("❌")
                await asyncio.sleep(0.67)
                await status_msg.delete()
                await message.delete()
                return
            
            doc = r
            origin = link
            
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    result = await self._load_module(
                        lm,
                        doc,
                        origin,
                        attempt
                    )
                    
                    if result == "success":
                        if lm.fully_loaded:
                            lm.update_modules_in_db()
                        
                        status_msg = await message.respond("✅")
                        await asyncio.sleep(0.5)
                        await status_msg.delete()
                        await message.delete()
                        return
                    
                    elif result == "retry":
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(0.33)
                            continue
                        else:
                            status_msg = await message.respond("📋")
                            await asyncio.sleep(1)
                            await status_msg.delete()
                            await message.delete()
                            return
                    
                    elif isinstance(result, dict) and result.get("type") == "requirements_error":
                        deps = result.get("deps", [])
                        if deps:
                            deps_text = ",".join(deps[:5])
                            status_msg = await message.respond(f"📋{deps_text}")
                        else:
                            status_msg = await message.respond("📋")
                        await asyncio.sleep(1)
                        await status_msg.delete()
                        await message.delete()
                        return
                    
                    elif result == "overwrite":
                        status_msg = await message.respond("😨")
                        await asyncio.sleep(1)
                        await status_msg.delete()
                        await message.delete()
                        return
                    
                    else:
                        status_msg = await message.respond("❌")
                        await asyncio.sleep(0.67)
                        await status_msg.delete()
                        await message.delete()
                        return
                        
                except Exception:
                    status_msg = await message.respond("❌")
                    await asyncio.sleep(0.67)
                    await status_msg.delete()
                    await message.delete()
                    return
            
            status_msg = await message.respond("📋")
            await asyncio.sleep(1)
            await status_msg.delete()
            await message.delete()
            
        except Exception:
            status_msg = await message.respond("❌")
            await asyncio.sleep(0.67)
            await status_msg.delete()
            await message.delete()

    async def _load_module(self, lm, doc, origin, attempt):
        if attempt == 0:
            requirements = []
            try:
                requirements = list(
                    filter(
                        lambda x: not x.startswith(("-", "_", ".")),
                        map(
                            lambda s: s.strip().rstrip(','),
                            loader.VALID_PIP_PACKAGES.search(doc)[1].split(),
                        ),
                    )
                )
            except (TypeError, AttributeError):
                pass
            
            if requirements:
                is_venv = hasattr(sys, 'real_prefix') or sys.prefix != getattr(sys, 'base_prefix', sys.prefix)
                need_user_flag = loader.USER_INSTALL and not is_venv
                
                pip = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "-q",
                    "--disable-pip-version-check",
                    "--no-warn-script-location",
                    *["--user"] if need_user_flag else [],
                    *requirements,
                )
                
                rc = await pip.wait()
                
                if rc != 0:
                    return {"type": "requirements_error", "deps": requirements}
                
                __import__('importlib').invalidate_caches()
                return "retry"
            
            packages = []
            try:
                packages = list(
                    filter(
                        lambda x: not x.startswith(("-", "_", ".")),
                        map(
                            lambda s: s.strip().rstrip(','),
                            loader.VALID_APT_PACKAGES.search(doc)[1].split(),
                        ),
                    )
                )
            except (TypeError, AttributeError):
                pass
            
            if packages:
                result = await lm.install_packages(packages)
                if not result:
                    return {"type": "requirements_error", "deps": packages}
                __import__('importlib').invalidate_caches()
                return "retry"
        
        try:
            node = ast.parse(doc)
            uid = next(
                n.name
                for n in node.body
                if isinstance(n, ast.ClassDef)
                and any(
                    isinstance(base, ast.Attribute)
                    and base.value.id == "Module"
                    or isinstance(base, ast.Name)
                    and base.id == "Module"
                    for base in n.bases
                )
            )
        except Exception:
            uid = "__extmod_" + str(uuid.uuid4())
        
        module_name = f"heroku.modules.{uid}"
        
        try:
            spec = ModuleSpec(
                module_name,
                loader.StringLoader(doc, f"<external {module_name}>"),
                origin=f"<external {module_name}>",
            )
            instance = await lm.allmodules.register_module(
                spec,
                module_name,
                origin,
                save_fs=False,
            )
        except ImportError as e:
            requirements = [
                {
                    "sklearn": "scikit-learn",
                    "pil": "Pillow",
                    "herokutl": "Heroku-TL-New",
                }.get(e.name.lower(), e.name)
            ]
            
            if not requirements:
                return "error"
            
            is_venv = hasattr(sys, 'real_prefix') or sys.prefix != getattr(sys, 'base_prefix', sys.prefix)
            need_user_flag = loader.USER_INSTALL and not is_venv
            
            pip = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "-q",
                "--disable-pip-version-check",
                "--no-warn-script-location",
                *["--user"] if need_user_flag else [],
                *requirements,
            )
            
            rc = await pip.wait()
            
            if rc != 0:
                return {"type": "requirements_error", "deps": requirements}
            
            __import__('importlib').invalidate_caches()
            return "retry"
            
        except CoreOverwriteError:
            with __import__('contextlib').suppress(Exception):
                await lm.allmodules.unload_module(instance.__class__.__name__)
            with __import__('contextlib').suppress(Exception):
                lm.allmodules.modules.remove(instance)
            return "overwrite"
        except (loader.LoadError, ScamDetectionError):
            with __import__('contextlib').suppress(Exception):
                await lm.allmodules.unload_module(instance.__class__.__name__)
            with __import__('contextlib').suppress(Exception):
                lm.allmodules.modules.remove(instance)
            return "error"
        except Exception:
            return "error"
        
        try:
            lm.allmodules.send_config_one(instance)
            
            await lm.allmodules.send_ready_one(
                instance,
                no_self_unload=True,
                from_dlmod=False,
            )
        except CoreOverwriteError:
            with __import__('contextlib').suppress(Exception):
                await lm.allmodules.unload_module(instance.__class__.__name__)
            with __import__('contextlib').suppress(Exception):
                lm.allmodules.modules.remove(instance)
            return "overwrite"
        except (loader.LoadError, ScamDetectionError, loader.SelfUnload, loader.SelfSuspend):
            with __import__('contextlib').suppress(Exception):
                await lm.allmodules.unload_module(instance.__class__.__name__)
            with __import__('contextlib').suppress(Exception):
                lm.allmodules.modules.remove(instance)
            return "error"
        except Exception:
            return "error"
        
        return "success"
