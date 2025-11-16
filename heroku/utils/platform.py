# ©️ Codrago, 2024-2025
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import contextlib
import logging
import os
import time
from datetime import timedelta

import herokutl

parser = herokutl.utils.sanitize_parse_mode("html")
logger = logging.getLogger(__name__)

IS_DOCKER = "DOCKER" in os.environ
IS_LAVHOST = "LAVHOST" in os.environ
IS_HIKKAHOST = "HIKKAHOST" in os.environ
IS_MACOS = "com.apple" in os.environ.get("PATH", "")
IS_USERLAND = "userland" in os.environ.get("USER", "")
IS_PTERODACTYL = "PTERODACTYL" in os.environ
IS_JAMHOST = "JAMHOST" in os.environ
IS_WSL = False
IS_WINDOWS = False
with contextlib.suppress(Exception):
    from platform import uname

    if "microsoft-standard" in uname().release:
        IS_WSL = True
    elif uname().system == "Windows":
        IS_WINDOWS = True


def get_named_platform() -> str:
    """
    Returns formatted platform name
    :return: Platform name
    """
    from .. import main

    with contextlib.suppress(Exception):
        if os.path.isfile("/proc/device-tree/model"):
            with open("/proc/device-tree/model") as f:
                model = f.read()
                if "Orange" in model:
                    return f"🍊 {model}"

                return f"🍇 {model}" if "Raspberry" in model else f"❓ {model}"

    if self.IS_WSL:
        return "🍀 WSL"

    if self.IS_WINDOWS:
        return "💻 Windows"

    if self.IS_MACOS:
        return "🍏 MacOS"

    if self.IS_JAMHOST:
        return "🧃 JamHost"

    if self.IS_USERLAND:
        return "🐧 UserLand"

    if self.IS_PTERODACTYL:
        return "🦅 Pterodactyl"
       
    if self.IS_HIKKAHOST:
        return "🌼 HikkaHost"

    if self.IS_DOCKER:
        return "🐳 Docker"

    return f"✌️ lavHost {os.environ['LAVHOST']}" if main.IS_LAVHOST else "💎 VDS"


def get_platform_emoji() -> str:
    """
    Returns custom emoji for current platform
    :return: Emoji entity in string
    """
    from .. import main

    BASE = "".join(
        (
            "<emoji document_id={}>🪐</emoji>",
            "<emoji document_id=5352934134618549768>🪐</emoji>",
            "<emoji document_id=5352663371290271790>🪐</emoji>",
            "<emoji document_id=5350822883314655367>🪐</emoji>",
        )
    )

    if main.IS_HIKKAHOST:
        return BASE.format(5395745114494624362)
    
    if main.IS_JAMHOST:
        return BASE.format(5242536621659678947)

    if main.IS_USERLAND:
        return BASE.format(5458877818031077824)

    if main.IS_PTERODACTYL:
        return BASE.format(5427286516797831670)
        
    if main.IS_LAVHOST:
        return BASE.format(5352753797531721191)

    if main.IS_DOCKER:
        return BASE.format(5352678227582152630)

    return BASE.format(5393588431026674882)

def uptime() -> int:
    """
    Returns userbot uptime in seconds
    """
    current_uptime = round(time.perf_counter() - init_ts)
    return current_uptime


def formatted_uptime() -> str:
    """
    Returns formatted uptime including days if applicable.
    :return: Formatted uptime
    """
    total_seconds = uptime()
    days, remainder = divmod(total_seconds, 86400)
    time_formatted = str(timedelta(seconds=remainder))
    if days > 0:
        return f"{days} day(s), {time_formatted}"
    return time_formatted


def get_ram_usage() -> float:
    """Returns current process tree memory usage in MB"""
    try:
        import psutil

        current_process = psutil.Process(os.getpid())
        mem = current_process.memory_info()[0] / 2.0**20
        for child in current_process.children(recursive=True):
            mem += child.memory_info()[0] / 2.0**20
        return round(mem, 1)
    except Exception:
        return 0

run_first_time = True # workaround 0.00% cpu usage
def get_cpu_usage():
    import psutil
    global run_first_time

    if run_first_time:
        try:
            psutil.cpu_count(logical=True)
            for proc in psutil.process_iter():
                try:
                    proc.cpu_percent()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception: pass
        run_first_time = False

    try:
        num_cores = psutil.cpu_count(logical=True)
        cpu = 0.0
        for proc in psutil.process_iter():
            try:
                cpu += proc.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        normalized_cpu = cpu / num_cores
        return f"{normalized_cpu:.2f}"
    except Exception:
        return "0.00"

init_ts = time.perf_counter()

get_platform_name = get_named_platform