# meta developer: @limokanews
# requires: whoosh

from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser, OrGroup
from whoosh.query import FuzzyTerm, Wildcard

import aiohttp
import random
import logging
import os
import html
import json
from datetime import datetime

from telethon.types import Message
from .. import utils, loader
from ..types import InlineQuery, InlineCall

logger = logging.getLogger("Limoka")

__version__ = (1, 1, 0)


class Search:
    def __init__(self, query, ix):
        self.schema = Schema(
            title=TEXT(stored=True), 
            path=ID(stored=True), 
            content=TEXT(stored=True)
        )
        self.query = query
        self.ix = ix

    def search_module(self, content=None):
        with self.ix.searcher() as searcher:
            parser = QueryParser("content", self.ix.schema, group=OrGroup.factory(0.8))
            query = parser.parse(self.query)
            wildcard_query = Wildcard("content", f"*{self.query}*")
            fuzzy_query = FuzzyTerm("content", self.query, maxdist=2, prefixlength=1)

            for search_query in [query, wildcard_query, fuzzy_query]:
                results = searcher.search(search_query)
                if results:
                    return list(set(result["path"] for result in results))
            return 0


class LimokaAPI:
    async def get_all_modules(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return json.loads(await response.text())


@loader.tds
class Limoka(loader.Module):
    """Hikka modules are now in one place with easy searching!"""

    strings = {
        "name": "Limoka",
        "wait": (
            "Just wait\n"
            "<emoji document_id=5404630946563515782>🔍</emoji> A search is underway among {count} modules "
            "for the query: <code>{query}</code>\n\n<i>{fact}</i>"
        ),
        "found": (
            "<emoji document_id=5413334818047940135>🔍</emoji> Found the module <b>{name}</b> "
            "by query: <b>{query}</b>\n\n"
            "<b><emoji document_id=5418376169055602355>ℹ️</emoji> Description:</b> {description}\n"
            "<b><emoji document_id=5418299289141004396>🧑‍💻</emoji> Developer:</b> {username}\n\n"
            "{commands}\n"
            "<emoji document_id=5411143117711624172>🪄</emoji> <code>{prefix}dlm {url}{module_path}</code>"
        ),
        "dotd": (
            "<emoji document_id=5436049557150655576>🌟</emoji> <b>Module of the Day</b>\n\n"
            "<emoji document_id=5413334818047940135>🔍</emoji> <b>{name}</b>\n"
            "<b><emoji document_id=5418376169055602355>ℹ️</emoji> Description:</b> {description}\n"
            "<b><emoji document_id=5418299289141004396>🧑‍💻</emoji> Developer:</b> {username}\n\n"
            "{commands}\n"
            "<emoji document_id=5411143117711624172>🪄</emoji> <code>{prefix}dlm {url}{module_path}</code>\n\n"
            "<i>Updates daily at midnight!</i>"
        ),
        "command_template": "{emoji} <code>{prefix}{command}</code> {description}\n",
        "emojis": {
            1: "<emoji document_id=5416037945909987712>1️⃣</emoji>",
            2: "<emoji document_id=5413855071731470617>2️⃣</emoji>",
            3: "<emoji document_id=5416068826724850291>3️⃣</emoji>",
            4: "<emoji document_id=5415843998071803071>4️⃣</emoji>",
            5: "<emoji document_id=5415684843763686989>5️⃣</emoji>",
            6: "<emoji document_id=5415975458430796879>6️⃣</emoji>",
            7: "<emoji document_id=5415769763857060166>7️⃣</emoji>",
            8: "<emoji document_id=5416006506749383505>8️⃣</emoji>",
            9: "<emoji document_id=5415963015910544694>9️⃣</emoji>",
        },
        "404": "<emoji document_id=5210952531676504517>❌</emoji> <b>Not found by query: <i>{query}</i></b>",
        "noargs": "<emoji document_id=5210952531676504517>❌</emoji> <b>No args</b>",
        "?": "<emoji document_id=5951895176908640647>🔎</emoji> Request too short / not found",
        "no_info": "No information",
        "facts": [
            "<emoji document_id=5472193350520021357>🛡</emoji> The limoka catalog is carefully moderated!",
            "<emoji document_id=5940434198413184876>🚀</emoji> Limoka performance allows you to search for modules quickly!",
        ],
        "inline404": "Not found",
        "inline?": "Request too short / not found",
        "inlinenoargs": "Please, enter query",
        "history": (
            "<emoji document_id=5879939498149679716>🔎</emoji> <b>Your search history:</b>\n"
            "{history}"
        ),
        "filter_menu": "Choose filters for query: <code>{query}</code>",
        "filter_cat": "📑 Filter by Category",
        "apply_filters": "✅ Apply Filters",
        "clear_filters": "🗑 Clear Filters",
        "back_to_results": "🔙 Back to Results",
        "empty_history": "<emoji document_id=5879939498149679716>🔎</emoji> <b>Your search history is empty!</b>",
    }

    strings_ru = {
        "wait": (
            "Подождите"
            "\n<emoji document_id=5404630946563515782>🔍</emoji> Идёт поиск среди {count} модулей по запросу: <code>{query}</code>"
            "\n"
            "\n<i>{fact}</i>"
        ),
        "found": (
            "<emoji document_id=5413334818047940135>🔍</emoji> Найден модуль <b>{name}</b> по запросу: <b>{query}</b>"
            "\n"
            "\n<b><emoji document_id=5418376169055602355>ℹ️</emoji> Описание:</b> {description}"
            "\n<b><emoji document_id=5418299289141004396>🧑‍💻</emoji> Разработчик:</b> {username}"
            "\n"
            "\n{commands}"
            "\n"
            "\n<emoji document_id=5411143117711624172>🪄</emoji> <code>{prefix}dlm {url}{module_path}</code>"
        ),
        "dotd": (
            "<emoji document_id=5436049557150655576>🌟</emoji> <b>Модуль дня</b>\n\n"
            "<emoji document_id=5413334818047940135>🔍</emoji> <b>{name}</b>\n"
            "<b><emoji document_id=5418376169055602355>ℹ️</emoji> Описание:</b> {description}\n"
            "<b><emoji document_id=5418299289141004396>🧑‍💻</emoji> Разработчик:</b> {username}\n\n"
            "{commands}\n"
            "<emoji document_id=5411143117711624172>🪄</emoji> <code>{prefix}dlm {url}{module_path}</code>\n\n"
            "<i>Обновляется ежедневно в полночь!</i>"
        ),
        "command_template": "{emoji} <code>{prefix}{command}</code> {description}\n",
        "404": "<emoji document_id=5210952531676504517>❌</emoji> <b>Не найдено по запросу: <i>{query}</i></b>",
        "noargs": "<emoji document_id=5210952531676504517>❌</emoji> <b>Нет аргументов</b>",
        "?": "<emoji document_id=5951895176908640647>🔎</emoji> Запрос слишком короткий / не найден",
        "no_info": "Нет информации",
        "facts": [
            "<emoji document_id=5472193350520021357>🛡</emoji> Каталог лимоки тщательно модерируется!",
            "<emoji document_id=5940434198413184876>🚀</emoji> Производительность лимоки позволяет вам искать модули с невероятной скоростью",
        ],
        "inline404": "Не найдено",
        "inline?": "Запрос слишком короткий / не найден",
        "inlinenoargs": "Введите запрос",
        "history": (
            "<emoji document_id=5879939498149679716>🔎</emoji> <b>История вашего поиска</b>:\n"
            "{history}"
        ),
        "filter_menu": "Выберите фильтры для запроса: <code>{query}</code>",
        "filter_cat": "📑 Фильтр по категории",
        "apply_filters": "✅ Применить фильтры",
        "clear_filters": "🗑 Очистить фильтры",
        "back_to_results": "🔙 Вернуться к результатам",
        "empty_history": "<emoji document_id=5879939498149679716>🔎</emoji> <b>Ваша история поиска пуста!</b>",
    }

    def __init__(self):
        self.api = LimokaAPI()
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "limoka_url",
                "https://git.vsecoder.dev/root/limoka/-/raw/main/",
                lambda: "Mirror: https://raw.githubusercontent.com/MuRuLOSE/limoka-mirror/refs/heads/main/",
                validator=loader.validators.String(),
            )
        )
        self.name = self.strings["name"]
        self._daily_module = None
        self._last_update = None

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.api = LimokaAPI()
        self.schema = Schema(
            title=TEXT(stored=True), 
            path=ID(stored=True), 
            content=TEXT(stored=True)
        )

        os.makedirs("limoka_search", exist_ok=True)
        self.ix = (
            create_in("limoka_search", self.schema)
            if not os.path.isdir("limoka_search/index")
            else open_dir("limoka_search")
        )

        self._history = self.pointer("history", [])
        self._daily_module_storage = self.pointer("daily_module", {"date": None, "path": None})
        self.modules = await self.api.get_all_modules(
            f"{self.config['limoka_url']}modules.json"
        )
        await self._update_index()
        await self._check_daily_module()

    async def _update_index(self):
        writer = self.ix.writer()
        for module_path, module_data in self.modules.items():
            for content in [module_data["name"], module_data["description"]]:
                writer.add_document(
                    title=module_data["name"],
                    path=module_path,
                    content=content
                )
            for func in module_data["commands"]:
                for command, description in func.items():
                    writer.add_document(
                        title=module_data["name"],
                        path=module_path,
                        content=command
                    )
                    writer.add_document(
                        title=module_data["name"],
                        path=module_path,
                        content=description
                    )
        writer.commit()

    async def _check_daily_module(self):
        """Проверяет и обновляет модуль дня если требуется"""
        current_date = datetime.now().date()
        stored_date = self._daily_module_storage.get("date")
        
        if not stored_date or datetime.strptime(stored_date, "%Y-%m-%d").date() != current_date:
            all_paths = list(self.modules.keys())
            random_path = random.choice(all_paths)
            self._daily_module = {
                "path": random_path,
                "info": self.modules[random_path]
            }
            self._daily_module_storage["date"] = current_date.strftime("%Y-%m-%d")
            self._daily_module_storage["path"] = random_path
        else:
            self._daily_module = {
                "path": self._daily_module_storage["path"],
                "info": self.modules[self._daily_module_storage["path"]]
            }

    def generate_commands(self, module_info):
        commands = []
        for i, func in enumerate(module_info["commands"], 1):
            if i > 9:
                commands.append("...")
                break
            for command, description in func.items():
                emoji = self.strings["emojis"].get(i, "")
                commands.append(
                    self.strings["command_template"].format(
                        prefix=self.get_prefix(),
                        command=html.escape(command.replace("cmd", "")),
                        emoji=emoji,
                        description=html.escape(description or self.strings["no_info"]),
                    )
                )
        return commands

    async def _display_filter_menu(self, call: InlineCall, query: str, current_filters: dict):
        markup = [
            [
                {"text": self.strings["filter_cat"], "callback": self._select_category, "args": (query, current_filters)},
            ],
            [
                {"text": self.strings["apply_filters"], "callback": self._apply_filters, "args": (query, current_filters)},
                {"text": self.strings["clear_filters"], "callback": self._clear_filters, "args": (query,)},
            ],
            [
                {"text": self.strings["back_to_results"], "callback": self._show_results, "args": (query, {})},
            ]
        ]
        
        categories = current_filters.get("category", [])
        filters_text = f"Categories: {', '.join(categories) if categories else 'None'}"
        await call.edit(
            self.strings["filter_menu"].format(query=query) + f"\n{filters_text}",
            reply_markup=markup
        )

    async def _select_category(self, call: InlineCall, query: str, current_filters: dict):
        all_categories = set()
        for module_data in self.modules.values():
            all_categories.update(module_data.get("category", []))
        categories = sorted(all_categories)

        if not categories:
            await call.edit("No categories found in the module database!", reply_markup=[])
            return

        selected_categories = current_filters.get("category", [])
        markup = [
            [{"text": f"{'✅ ' if cat in selected_categories else ''}{cat}", 
              "callback": self._toggle_category, 
              "args": (query, current_filters, cat)}]
            for cat in categories
        ]
        markup.append([{"text": "🔙 Back", "callback": self._display_filter_menu, "args": (query, current_filters)}])
        
        await call.edit(
            f"Select categories for query: <code>{query}</code>\n(You can select multiple)",
            reply_markup=markup
        )

    async def _toggle_category(self, call: InlineCall, query: str, current_filters: dict, category: str):
        new_filters = current_filters.copy()
        selected_categories = new_filters.get("category", [])
        
        if category in selected_categories:
            selected_categories.remove(category)
        else:
            selected_categories.append(category)
        
        if selected_categories:
            new_filters["category"] = selected_categories
        else:
            new_filters.pop("category", None)
        
        await self._select_category(call, query, new_filters)

    async def _apply_filters(self, call: InlineCall, query: str, filters: dict):
        await self._show_results(call, query, filters, from_filters=True)

    async def _clear_filters(self, call: InlineCall, query: str):
        await self._show_results(call, query, {}, from_filters=True)

    async def _show_results(self, call: InlineCall, query: str, filters: dict, from_filters: bool = False):
        searcher = Search(query.lower(), self.ix)
        try:
            result = searcher.search_module()
        except IndexError:
            await call.edit(self.strings["?"], reply_markup=[])
            return

        if not result or result == 0:
            if from_filters:
                markup = [[{"text": "🔙 Back", "callback": self._display_filter_menu, "args": (query, filters)}]]
                await call.edit(self.strings["404"].format(query=query), reply_markup=markup)
            else:
                await call.edit(self.strings["404"].format(query=query), reply_markup=[])
            return

        if filters.get("category"):
            filtered_result = [
                path for path in result 
                if any(cat in self.modules.get(path, {}).get("category", []) for cat in filters["category"])
            ]
        else:
            filtered_result = result

        if not filtered_result:
            if from_filters:
                markup = [[{"text": "🔙 Back", "callback": self._display_filter_menu, "args": (query, filters)}]]
                await call.edit(self.strings["404"].format(query=query), reply_markup=markup)
            else:
                await call.edit(self.strings["404"].format(query=query), reply_markup=[])
            return

        module_path = filtered_result[0]
        module_info = self.modules[module_path]
        await self._display_module(call, module_info, module_path, query, filtered_result, 0, filters)

    @loader.command()
    async def limokacmd(self, message: Message):
        """[query] - Search module with filter options"""
        args = utils.get_args_raw(message)
        if len(self._history) == 10:
            self._history.pop(0)

        if len(args) <= 1:
            return await utils.answer(message, self.strings["?"])
        if not args:
            return await utils.answer(message, self.strings["noargs"])

        self._history.append(args)

        await utils.answer(
            message,
            self.strings["wait"].format(
                count=len(self.modules),
                fact=random.choice(self.strings["facts"]),
                query=args,
            ),
        )

        searcher = Search(args.lower(), self.ix)
        try:
            result = searcher.search_module()
        except IndexError:
            return await utils.answer(message, self.strings["?"])

        if not result or result == 0:
            return await utils.answer(message, self.strings["404"].format(query=args))

        module_path = result[0]
        module_info = self.modules[module_path]
        await self._display_module(message, module_info, module_path, args, result, 0, {})

    @loader.command()
    async def lshistorycmd(self, message: Message):
        """ - Showing the last 10 requests"""
        if not self._history:
            await utils.answer(message, self.strings["empty_history"])
            return

        formatted_history = [f"{i+1}. <code>{history}</code>" for i, history in enumerate(self._history)]
        await utils.answer(
            message, 
            self.strings["history"].format(
                history='\n'.join(formatted_history)
            )
        )

    @loader.command()
    async def limokadotd(self, message: Message):
        """- Show the Module of the Day"""
        await self._check_daily_module()
        
        if not self._daily_module:
            await utils.answer(message, "Error loading module of the day!")
            return

        module_info = self._daily_module["info"]
        module_path = self._daily_module["path"]
        
        dev_username = module_info["meta"].get("developer", "Unknown")
        name = module_info["name"] or self.strings["no_info"]
        description = html.escape(module_info["description"] or self.strings["no_info"])
        commands = self.generate_commands(module_info)
        banner = module_info["meta"].get("banner")

        formatted_message = self.strings["dotd"].format(
            name=name,
            description=description,
            url=self.config["limoka_url"],
            username=dev_username,
            commands="".join(commands),
            prefix=self.get_prefix(),
            module_path=module_path.replace("\\", "/"),
        )

        await self.inline.form(
            formatted_message,
            message,
            photo=banner or None
        )

    async def _display_module(self, message_or_call, module_info, module_path, query, result, index, filters):
        dev_username = module_info["meta"].get("developer", "Unknown")
        name = module_info["name"] or self.strings["no_info"]
        description = html.escape(module_info["description"] or self.strings["no_info"])
        banner = module_info["meta"].get("banner")
        commands = self.generate_commands(module_info)
        page = index + 1

        clean_module_path = module_path.replace('\\', '/')

        formatted_message = self.strings["found"].format(
            query=query,
            name=name,
            description=description,
            url=self.config["limoka_url"],
            username=dev_username,
            commands="".join(commands),
            prefix=self.get_prefix(),
            module_path=clean_module_path,
        )

        categories = filters.get("category", [])
        filters_text = f"Categories: {', '.join(categories) if categories else 'None'}"

        full_message = formatted_message + f"\n{filters_text}"
        if len(full_message) > 1024:
            download_command = f"<emoji document_id=5411143117711624172>🪄</emoji> <code>{self.get_prefix()}dlm {self.config['limoka_url']}{clean_module_path}</code>"
            max_content_length = 1024 - len(f"\n{download_command}\n{filters_text}") - 50
            if max_content_length < 100:
                max_content_length = 100
            
            description = (description[:max_content_length//2] + "...") if len(description) > max_content_length//2 else description
            commands = commands[:3] if len(commands) > 3 else commands
            formatted_message = (
                f"<emoji document_id=5413334818047940135>🔍</emoji> Found the module <b>{name}</b> "
                f"by query: <b>{query}</b>\n\n"
                f"<b><emoji document_id=5418376169055602355>ℹ️</emoji> Description:</b> {description}\n"
                f"<b><emoji document_id=5418299289141004396>🧑‍💻</emoji> Developer:</b> {dev_username}\n\n"
                f"{''.join(commands)}\n"
            ).strip()
            full_message = f"{formatted_message[:max_content_length]}{'...' if len(formatted_message) > max_content_length else ''}\n\n{download_command}\n{filters_text}"
        else:
            full_message = formatted_message + f"\n{filters_text}"

        markup = [
            [
                {
                    "text": "⏪" if index > 0 else "🚫",
                    "callback": self._previous_page if index > 0 else self._inline_void,
                    "args": (result, index, query, filters) if index > 0 else (),
                },
                {"text": f"{page}/{len(result)}", "callback": self._inline_void},
                {
                    "text": "⏩" if index + 1 < len(result) else "🚫",
                    "callback": self._next_page if index + 1 < len(result) else self._inline_void,
                    "args": (result, index, query, filters) if index + 1 < len(result) else (),
                },
            ],
            [
                {"text": "🔍 Filters", "callback": self._display_filter_menu, "args": (query, filters)},
            ]
        ]


        if isinstance(message_or_call, Message):
            await self.inline.form(
                full_message, message_or_call, reply_markup=markup, photo=banner or None
            )
        else:
            if banner:
                await message_or_call.edit(
                    full_message,
                    reply_markup=markup,
                    photo=banner
                )
            else:
                await message_or_call.edit(
                    full_message,
                    reply_markup=markup,
                    photo=None
                )

    async def _next_page(self, call: InlineCall, result: list, index: int, query: str, filters: dict):
        if index + 1 >= len(result):
            await call.answer("This is the last page!")
            return

        index += 1
        module_path = result[index]
        module_info = self.modules[module_path]
        await self._display_module(call, module_info, module_path, query, result, index, filters)

    async def _previous_page(self, call: InlineCall, result: list, index: int, query: str, filters: dict):
        if index - 1 < 0:
            await call.answer("This is the first page!")
            return

        index -= 1
        module_path = result[index]
        module_info = self.modules[module_path]
        await self._display_module(call, module_info, module_path, query, result, index, filters)

    async def _inline_void(self, call: InlineCall):
        await call.answer()

    @loader.inline_handler()
    async def limoka(self, query: InlineQuery):
        """[query] - Inline search modules"""
        if not query.args:
            return {
                "title": "No query",
                "description": self.strings["inlinenoargs"],
                "thumb": "https://img.icons8.com/?size=100&id=NIWYFnJlcBfr&format=png&color=000000",
                "message": self.strings["inlinenoargs"],
            }

        searcher = Search(query.args.lower(), self.ix)
        try:
            results = searcher.search_module()
        except IndexError:
            return {
                "title": "Something went wrong...",
                "description": self.strings["inline?"],
                "thumb": "https://img.icons8.com/?size=100&id=rUSWMuGVdxJj&format=png&color=000000",
                "message": self.strings["inline?"],
            }

        if not results:
            return {
                "title": "No results",
                "description": self.strings["inline404"],
                "thumb": "https://img.icons8.com/?size=100&id=olDsW0G3zz22&format=png&color=000000",
                "message": self.strings["inline404"],
            }

        inline_results = []
        for path in results:
            module_info = self.modules.get(path)
            if module_info and module_info.get("commands"):
                inline_results.append(
                    {
                        "title": utils.escape_html(module_info["name"]),
                        "description": utils.escape_html(module_info["description"]),
                        "thumb": module_info["meta"].get(
                            "pic",
                            "https://img.icons8.com/?size=100&id=olDsW0G3zz22&format=png&color=000000",
                        ),
                        "photo": module_info["meta"].get(
                            "banner",
                            "https://habrastorage.org/getpro/habr/upload_files/9c7/5fa/c54/9c75fac54ebb0beaf89abd7d86b4787c.jpg",
                        ),
                        "message": self.strings["found"].format(
                            name=module_info["name"],
                            query=query.args,
                            url=self.config["limoka_url"],
                            description=module_info["description"],
                            username=module_info["meta"].get("developer", "Unknown"),
                            commands="".join(self.generate_commands(module_info)),
                            module_path=path.replace("\\", "/"),
                            prefix=self.get_prefix(),
                        ),
                    }
                )
        return inline_results