# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import contextlib
import logging
import os
import random
import sys
import traceback
from threading import Thread

from werkzeug import Request, Response
from werkzeug.debug import DebuggedApplication
from werkzeug.serving import BaseWSGIServer, make_server

from .. import main, utils
from . import proxypass

logger = logging.getLogger(__name__)


class ServerThread(Thread):
    def __init__(self, server: BaseWSGIServer):
        super().__init__(daemon=True)
        self.server = server

    def run(self):
        logger.debug("Starting werkzeug debug server")
        try:
            self.server.serve_forever()
        except Exception as e:
            logger.error("Werkzeug server error: %s", e)

    def shutdown(self):
        logger.debug("Shutting down werkzeug debug server")
        with contextlib.suppress(Exception):
            self.server.shutdown()


class WebDebugger:
    def __init__(self):
        self._url = None
        self.exceptions = {}
        self.pin = str(random.randint(100000, 999999))
        self.port = main.gen_port("werkzeug_port", True)
        main.save_config_key("werkzeug_port", self.port)
        self._proxypasser = proxypass.ProxyPasser(self._url_changed)
        self.proxy_ready = asyncio.Event()
        asyncio.ensure_future(self._getproxy())
        self._server = self._create_server()
        self._controller = ServerThread(self._server)
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        self._controller.start()
        utils.atexit(self._controller.shutdown)

    async def _getproxy(self):
        try:
            self._url = await self._proxypasser.get_url(self.port)
        except Exception as e:
            logger.warning("Failed to get proxy URL: %s", e)
            self._url = f"http://127.0.0.1:{self.port}"
        self.proxy_ready.set()

    def _url_changed(self, url: str):
        logger.info("WebDebugger URL changed: %s", url)
        self._url = url

    def _create_server(self) -> BaseWSGIServer:
        logger.debug("Creating new werkzeug server instance")
        os.environ["WERKZEUG_DEBUG_PIN"] = self.pin
        os.environ["WERKZEUG_RUN_MAIN"] = "true"

        @Request.application
        def app(request):
            if request.args.get("ping", "N").upper() == "Y":
                return Response("ok")

            if request.args.get("shutdown", "N").upper() == "Y":
                self._server._BaseServer__shutdown_request = True
                return Response("Shutdown!")

            ex_id = request.args.get("ex_id")
            if ex_id and ex_id in self.exceptions:
                exc = self.exceptions[ex_id]
                raise exc
            return Response("No exception found", status=404)

        app = DebuggedApplication(app, evalex=True, pin_security=True)

        try:
            fd = int(os.environ.get("WERKZEUG_SERVER_FD", ""))
        except (TypeError, ValueError):
            fd = None

        server = make_server(
            "localhost",
            self.port,
            app,
            threaded=False,
            processes=1,
            request_handler=None,
            passthrough_errors=False,
            ssl_context=None,
            fd=fd,
        )

        return server

    @property
    def url(self) -> str:
        return self._url or f"http://127.0.0.1:{self.port}"

    def feed(self, exc_type, exc_value, exc_traceback) -> str:
        logger.debug("Feeding exception %s to werkzeug debugger", exc_type)
        ex_id = utils.rand(8)
        # Восстанавливаем исключение с трейсбеком
        try:
            exc = exc_type(exc_value)
            if hasattr(exc, "with_traceback"):
                exc = exc.with_traceback(exc_traceback)
        except Exception:
            exc = Exception(str(exc_value))
        self.exceptions[ex_id] = exc
        return self.url.rstrip("/") + f"?ex_id={ex_id}"
