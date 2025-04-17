"""Responsible for web init and mandatory ops"""

import asyncio
import contextlib
import inspect
import logging
import os
import subprocess

import aiohttp_jinja2
import jinja2
from aiohttp import web

from ..database import Database
from ..loader import Modules
from ..tl_cache import CustomTelegramClient
from . import proxypass, root

logger = logging.getLogger(__name__)


class Web(root.Web):
    def __init__(self, **kwargs):
        self.runner: web.AppRunner = None
        self.port: int = None
        self.running = asyncio.Event()
        self.ready = asyncio.Event()
        self.client_data = {}
        self.app = web.Application()
        self.proxypasser = None
        aiohttp_jinja2.setup(
            self.app,
            filters={"getdoc": inspect.getdoc, "ascii": ascii},
            loader=jinja2.FileSystemLoader("web-resources"),
        )
        self.app["static_root_url"] = "/static"

        super().__init__(**kwargs)
        self.app.router.add_get("/favicon.ico", self.favicon)
        self.app.router.add_static("/static/", "web-resources/static")

    async def start_if_ready(
        self,
        total_count: int,
        port: int,
        proxy_pass: bool = False,
    ):
        """
        Запускает веб, если все клиенты добавлены.
        """
        if total_count <= len(self.client_data):
            if not self.running.is_set():
                await self.start(port, proxy_pass=proxy_pass)
            self.ready.set()

    async def get_url(self, proxy_pass: bool) -> str:
        """
        Получить URL веб-интерфейса.
        """
        url = None

        if all(option in os.environ for option in {"LAVHOST", "USER", "SERVER"}):
            url = f"https://{os.environ['USER']}.{os.environ['SERVER']}.lavhost.ml"
            self.url = url
            return url

        if proxy_pass and self.proxypasser:
            with contextlib.suppress(Exception):
                url = await self.proxypasser.get_url(timeout=10)

        if not url:
            if "DOCKER" in os.environ:
                try:
                    ip = (
                        subprocess.run(
                            ["hostname", "-I"],
                            stdout=subprocess.PIPE,
                            check=True,
                        )
                        .stdout.decode("utf-8")
                        .strip()
                        .split()[0]
                    )
                except Exception:
                    ip = "127.0.0.1"
            else:
                try:
                    ip = (
                        subprocess.run(
                            ["hostname", "-i"],
                            stdout=subprocess.PIPE,
                            check=True,
                        )
                        .stdout.decode("utf-8")
                        .strip()
                    )
                except Exception:
                    ip = "127.0.0.1"

            url = f"http://{ip}:{self.port}"

        self.url = url
        logger.info(f"Web interface available at: {url}")
        return url

    async def start(self, port: int, proxy_pass: bool = False):
        """
        Запуск веб-сервера.
        """
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.port = int(os.environ.get("PORT", port))
        site = web.TCPSite(self.runner, None, self.port)
        self.proxypasser = proxypass.ProxyPasser(port=self.port)
        await site.start()

        await self.get_url(proxy_pass)
        self.running.set()
        logger.info("Web server started on port %s", self.port)

    async def stop(self):
        """
        Остановка веб-сервера.
        """
        if self.runner:
            await self.runner.shutdown()
            await self.runner.cleanup()
            self.runner = None
        self.running.clear()
        self.ready.clear()
        logger.info("Web server stopped")

    async def add_loader(
        self,
        client: CustomTelegramClient,
        loader: Modules,
        db: Database,
    ):
        """
        Добавить клиента и его загрузчик в веб-интерфейс.
        """
        self.client_data[client.tg_id] = (loader, client, db)
        logger.debug("Added loader for client %s", client.tg_id)

    @staticmethod
    async def favicon(_):
        """
        Редирект на фавикон.
        """
        return web.Response(
            status=301,
            headers={"Location": "https://i.imgur.com/IRAiWBo.jpeg"},
        )
