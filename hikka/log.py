"""Main logging part"""

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
import contextlib
import inspect
import io
import linecache
import logging
import os
import re
import sys
import traceback
import typing
from datetime import datetime
from logging.handlers import RotatingFileHandler

import herokutl
from aiogram.utils.exceptions import NetworkError
from herokutl.errors import PersistentTimestampOutdatedError

from . import utils
from .tl_cache import CustomTelegramClient
from .types import BotInlineCall, Module
from .web.debugger import WebDebugger

COLORS = {
    "DEBUG": "\033[36m",  # Cyan
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[31;1m",  # Bright Red
    "RESET": "\033[0m",  # Reset
}

EMOJIS = {
    "DEBUG": "🐛",
    "INFO": "ℹ️",
    "WARNING": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "💥",
}

old_getlines = linecache.getlines


def getlines(filename: str, module_globals=None) -> typing.List[str]:
    """Enhanced version of linecache.getlines with Heroku modules support"""
    try:
        if filename.startswith("<") and filename.endswith(">"):
            module = filename[1:-1].split(maxsplit=1)[-1]
            if (module.startswith("hikka.modules")) and module in sys.modules:
                loader = getattr(sys.modules[module], "__loader__", None)
                if loader and hasattr(loader, "get_source"):
                    return [f"{x}\n" for x in loader.get_source().splitlines()]
    except Exception:
        logging.debug("Can't get lines for %s", filename, exc_info=True)

    return old_getlines(filename, module_globals)


linecache.getlines = getlines


def override_text(exception: Exception) -> typing.Optional[str]:
    """Returns user-friendly error descriptions for specific exceptions"""
    if isinstance(exception, (NetworkError, asyncio.exceptions.TimeoutError)):
        return "🌐 <b>Connection Error:</b> Problems with internet connection on your server."
    elif isinstance(exception, PersistentTimestampOutdatedError):
        return "⚡ <b>Telegram DC Issue:</b> Problems with Telegram datacenters."
    return None


class EnhancedException:
    """Enhanced exception formatting with rich traceback information"""

    def __init__(
        self,
        message: str,
        full_stack: str,
        sysinfo: typing.Optional[
            typing.Tuple[object, Exception, traceback.TracebackException]
        ] = None,
    ):
        self.message = message
        self.full_stack = full_stack
        self.sysinfo = sysinfo
        self.debug_url = None
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def from_exc_info(
        cls,
        exc_type: object,
        exc_value: Exception,
        tb: traceback.TracebackException,
        stack: typing.Optional[typing.List[inspect.FrameInfo]] = None,
        comment: typing.Optional[typing.Any] = None,
    ) -> "EnhancedException":
        """Create EnhancedException from exception info"""

        def sanitize_value(value: typing.Any) -> str:
            """Sanitize values for safe logging"""
            if value is None:
                return "None"
            elif isinstance(value, (str, int, float, bool)):
                return str(value)
            elif isinstance(value, dict):
                return "{...}"
            elif hasattr(value, "__class__"):
                return f"<{value.__class__.__name__}>"
            return str(value)[:512] + "..." if len(str(value)) > 512 else str(value)

        full_traceback = traceback.format_exc().replace(
            "Traceback (most recent call last):\n", ""
        )

        line_regex = re.compile(r'  File "(.*?)", line ([0-9]+), in (.+)')

        def format_traceback_line(line: str) -> str:
            """Format a single traceback line with HTML"""
            match = line_regex.search(line)
            if not match:
                return f"<code>{utils.escape_html(line)}</code>"

            filename_, lineno_, name_ = match.groups()
            return (
                f"🔹 <code>{utils.escape_html(filename_)}:{lineno_}</code> "
                f"<b>in</b> <code>{utils.escape_html(name_)}</code>"
            )

        formatted_traceback = "\n".join(
            format_traceback_line(line) for line in full_traceback.splitlines()
        )

        filename, lineno, name = next(
            (
                line_regex.search(line).groups()
                for line in reversed(full_traceback.splitlines())
                if line_regex.search(line)
            ),
            (None, None, None),
        )

        caller = utils.find_caller(stack or inspect.stack())
        caller_info = ""
        if caller and hasattr(caller, "__self__") and hasattr(caller, "__name__"):
            caller_info = (
                f"🔮 <b>Called by:</b> <code>{utils.escape_html(caller.__name__)}</code> "
                f"in <code>{utils.escape_html(caller.__self__.__class__.__name__)}</code>\n\n"
            )

        error_msg = override_text(exc_value) or (
            f"{caller_info}"
            f"📌 <b>Location:</b> <code>{utils.escape_html(filename)}:{lineno}</code> "
            f"in <code>{utils.escape_html(name)}</code>\n"
            f"🚨 <b>Error:</b> <code>{utils.escape_html(''.join(traceback.format_exception_only(exc_type, exc_value))).strip()}</code>"
            f"{f'\n💬 <b>Note:</b> <code>{utils.escape_html(str(comment))}</code>' if comment else ''}"
        )

        return cls(
            message=error_msg,
            full_stack=formatted_traceback,
            sysinfo=(exc_type, exc_value, tb),
        )


class ColorFormatter(logging.Formatter):
    """Log formatter that adds colors and emojis to terminal output"""

    def format(self, record):
        levelname = record.levelname
        emoji = EMOJIS.get(levelname, "🔹")
        color = COLORS.get(levelname, COLORS["RESET"])

        record.levelname = f"{color}{emoji} {levelname}{COLORS['RESET']}"
        record.name = f"\033[35m{record.name}{COLORS['RESET']}"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record.msg = (
            f"\033[2m{timestamp}\033[0m {record.levelname} {record.name}: {record.msg}"
        )

        return super().format(record)


class TelegramLogsHandler(logging.Handler):
    """Handler for sending logs to Telegram with rich formatting"""

    def __init__(self, targets: tuple, capacity: int):
        super().__init__(0)
        self.buffer = []
        self.handledbuffer = []
        self._queue = {}
        self._mods = {}
        self.tg_buff = []
        self.force_send_all = False
        self.tg_level = logging.WARNING
        self.ignore_common = False
        self.web_debugger = None
        self.targets = targets
        self.capacity = capacity
        self.lvl = logging.NOTSET
        self._send_lock = asyncio.Lock()
        self._task = None

    def install_tg_log(self, mod: Module):
        """Install Telegram logging for a module"""
        if self._task:
            self._task.cancel()

        self._mods[mod.tg_id] = mod

        if getattr(mod.db, "get", lambda *a, **k: False)(__name__, "debugger", False):
            self.web_debugger = WebDebugger()

        self._task = asyncio.ensure_future(self.queue_poller())

    async def queue_poller(self):
        """Periodically send logs to Telegram"""
        while True:
            try:
                await self.sender()
            except Exception as e:
                logging.error("Error in queue_poller: %s", e)
            await asyncio.sleep(3)

    def setLevel(self, level: int):
        """Set the minimum logging level"""
        self.lvl = level

    def dump(self):
        """Return all log records"""
        return self.handledbuffer + self.buffer

    def dumps(
        self, lvl: int = 0, client_id: typing.Optional[int] = None
    ) -> typing.List[str]:
        """Return formatted log messages"""
        return [
            self.targets[0].format(record)
            for record in (self.buffer + self.handledbuffer)
            if record.levelno >= lvl
            and (
                not getattr(record, "hikka_caller", None)
                or client_id == getattr(record, "hikka_caller", None)
            )
        ]

    async def _show_full_trace(
        self,
        call: BotInlineCall,
        bot: "aiogram.Bot",  # type: ignore
        item: EnhancedException,
    ):
        """Show full traceback in Telegram"""
        chunks = (
            f"⏰ <b>Time:</b> <code>{item.timestamp}</code>\n"
            f"{item.message}\n\n"
            f"📜 <b>Full traceback:</b>\n"
            f"{item.full_stack}"
        )

        chunks = list(utils.smart_split(*herokutl.extensions.html.parse(chunks), 4096))

        await call.edit(
            chunks[0],
            reply_markup=self._gen_web_debug_button(item),
        )

        for chunk in chunks[1:]:
            await bot.send_message(chat_id=call.chat_id, text=chunk)

    def _gen_web_debug_button(self, item: EnhancedException) -> list:
        """Generate web debugger button for Telegram"""
        if not item.sysinfo:
            return []

        url = item.debug_url
        if not url:
            try:
                url = (
                    self.web_debugger.feed(*item.sysinfo) if self.web_debugger else None
                )
            except Exception:
                url = None
            item.debug_url = url

        if url:
            return [
                {
                    "text": "🐞 Web Debugger",
                    "url": url,
                }
            ]
        else:
            return [
                {
                    "text": "🪲 Start Debugger",
                    "callback": self._start_debugger,
                    "args": (item,),
                }
            ]

    async def _start_debugger(self, call: "BotInlineCall", item: EnhancedException):
        """Start web debugger and update message"""
        if not self.web_debugger:
            self.web_debugger = WebDebugger()
            await self.web_debugger.proxy_ready.wait()

        url = self.web_debugger.feed(*item.sysinfo)
        item.debug_url = url

        await call.edit(
            item.message,
            reply_markup=self._gen_web_debug_button(item),
        )

        await call.answer(
            "Web debugger started. Use .debugger command to get PIN.\n"
            "⚠️ DO NOT SHARE THE PIN WITH ANYONE! ⚠️",
            show_alert=True,
        )

    def get_logid_by_client(self, client_id: int) -> int:
        """Get log chat ID for a client"""
        return self._mods[client_id].logchat

    async def sender(self):
        """Send buffered logs to Telegram"""
        async with self._send_lock:
            if not self._mods:
                return

            # Формируем очереди сообщений
            self._queue = {
                client_id: utils.chunks(
                    "\n".join(
                        f"⏰ <b>{datetime.now().strftime('%H:%M:%S')}</b> | "
                        f"{EMOJIS.get(getattr(record, 'levelname', ''), '🔹')} "
                        f"<code>{utils.escape_html(self.targets[1].format(record))}</code>"
                        for record in [
                            item[0]
                            for item in self.tg_buff
                            if isinstance(item[0], logging.LogRecord)
                            and (
                                not item[1]
                                or item[1] == client_id
                                or self.force_send_all
                            )
                        ]
                    ),
                    4096,
                )
                for client_id in self._mods
            }

            self._exc_queue = {
                client_id: [
                    self._mods[client_id].inline.bot.send_message(
                        self._mods[client_id].logchat,
                        f"⏰ <b>Time:</b> <code>{item[0].timestamp}</code>\n"
                        f"{item[0].message}",
                        reply_markup=self._mods[client_id].inline.generate_markup(
                            [
                                {
                                    "text": "📜 Full Traceback",
                                    "callback": self._show_full_trace,
                                    "args": (self._mods[client_id].inline.bot, item[0]),
                                    "disable_security": True,
                                },
                                *self._gen_web_debug_button(item[0]),
                            ]
                        ),
                    )
                    for item in self.tg_buff
                    if isinstance(item[0], EnhancedException)
                    and (not item[1] or item[1] == client_id or self.force_send_all)
                ]
                for client_id in self._mods
            }

            # Отправка исключений
            for exceptions in self._exc_queue.values():
                for exc in exceptions:
                    try:
                        await exc
                    except Exception as e:
                        logging.error("Failed to send exception to Telegram: %s", e)

            self.tg_buff = []

            # Отправка обычных логов
            for client_id in self._mods:
                if not self._queue.get(client_id):
                    continue

                if len(self._queue[client_id]) > 5:
                    logfile = io.BytesIO(
                        "\n".join(self._queue[client_id]).encode("utf-8")
                    )
                    logfile.name = (
                        f"heroku-logs-{datetime.now().strftime('%Y-%m-%d')}.txt"
                    )
                    logfile.seek(0)

                    try:
                        await self._mods[client_id].inline.bot.send_document(
                            self._mods[client_id].logchat,
                            logfile,
                            caption="📁 <b>Logs are too large for messages</b>",
                        )
                    except Exception as e:
                        logging.error("Failed to send log file: %s", e)

                    self._queue[client_id] = []
                    continue

                for chunk in self._queue[client_id]:
                    if chunk:
                        try:
                            await self._mods[client_id].inline.bot.send_message(
                                self._mods[client_id].logchat,
                                f"<code>{chunk}</code>",
                                disable_notification=True,
                            )
                        except Exception as e:
                            logging.error("Failed to send log message: %s", e)

    def emit(self, record: logging.LogRecord):
        """Handle a log record"""
        try:
            caller = next(
                (
                    frame_info.frame.f_locals["_hikka_client_id_logging_tag"]
                    for frame_info in inspect.stack()
                    if isinstance(
                        frame_info.frame.f_locals.get("_hikka_client_id_logging_tag"),
                        int,
                    )
                ),
                None,
            )
        except Exception:
            caller = None

        record.hikka_caller = caller

        if record.levelno >= self.tg_level and record.exc_info:
            exc = EnhancedException.from_exc_info(
                *record.exc_info,
                stack=record.__dict__.get("stack", None),
                comment=record.getMessage(),
            )

            if not self.ignore_common or all(
                field not in exc.message
                for field in [
                    "InputPeerEmpty() does not have any entity type",
                    "https://docs.telethon.dev/en/stable/concepts/entities.html",
                ]
            ):
                self.tg_buff.append((exc, caller))
        elif record.levelno >= self.tg_level:
            self.tg_buff.append(
                (
                    record,
                    caller,
                )
            )

        if len(self.buffer) + len(self.handledbuffer) >= self.capacity:
            if self.handledbuffer:
                del self.handledbuffer[0]
            else:
                del self.buffer[0]

        self.buffer.append(record)

        if record.levelno >= self.lvl >= 0:
            self.acquire()
            try:
                for precord in self.buffer:
                    for target in self.targets:
                        if record.levelno >= getattr(target, "level", logging.NOTSET):
                            target.handle(precord)

                self.handledbuffer = (
                    self.handledbuffer[-(self.capacity - len(self.buffer)) :]
                    + self.buffer
                )
                self.buffer = []
            finally:
                self.release()


_main_formatter = ColorFormatter(
    fmt="%(levelname)s %(name)s: %(message)s",
    datefmt=None,
    style="%",
)

_plain_formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    style="%",
)

_tg_formatter = logging.Formatter(
    fmt="[%(levelname)s] %(name)s: %(message)s",
    datefmt=None,
    style="%",
)

rotating_handler = RotatingFileHandler(
    filename="heroku.log",
    mode="a",
    maxBytes=10 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
    delay=False,
)
rotating_handler.setFormatter(_plain_formatter)


def init():
    """Initialize the logging system"""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(_main_formatter)

    logging.getLogger().handlers = []
    logging.getLogger().addHandler(
        TelegramLogsHandler((console_handler, rotating_handler), 7000)
    )
    logging.getLogger().setLevel(logging.NOTSET)

    logging.getLogger("herokutl").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)

    logging.captureWarnings(True)
