# ©️ Codrago, 2024-2025
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import atexit as _atexit
import contextlib
import functools
import inspect
import io
import json
import logging
import os
import random
import re
import shlex
import signal
import string
import time
import typing
from datetime import timedelta
from urllib.parse import urlparse
import emoji

import git
import grapheme
import herokutl
import herokutl.extensions
import herokutl.extensions.html
import requests
from aiogram.types import Message as AiogramMessage
from herokutl import hints
from herokutl.tl.custom.message import Message
from herokutl.tl.functions.account import UpdateNotifySettingsRequest
from herokutl.tl.functions.channels import (
    CreateChannelRequest,
    EditAdminRequest,
    EditPhotoRequest,
    InviteToChannelRequest,
)
from herokutl.tl.functions.messages import (
    GetDialogFiltersRequest,
    SetHistoryTTLRequest,
    UpdateDialogFilterRequest,
)
from herokutl.tl.types import (
    Channel,
    Chat,
    ChatAdminRights,
    InputDocument,
    InputPeerNotifySettings,
    MessageEntityBankCard,
    MessageEntityBlockquote,
    MessageEntityBold,
    MessageEntityBotCommand,
    MessageEntityCashtag,
    MessageEntityCode,
    MessageEntityEmail,
    MessageEntityHashtag,
    MessageEntityItalic,
    MessageEntityMention,
    MessageEntityMentionName,
    MessageEntityPhone,
    MessageEntityPre,
    MessageEntitySpoiler,
    MessageEntityStrike,
    MessageEntityTextUrl,
    MessageEntityUnderline,
    MessageEntityUnknown,
    MessageEntityUrl,
    MessageMediaPhoto,
    MessageMediaDocument,
    MessageMediaWebPage,
    PeerChannel,
    PeerChat,
    PeerUser,
    UpdateNewChannelMessage,
    User,
)

from .._internal import fw_protect
from ..inline.types import BotInlineCall, InlineCall, InlineMessage
from ..tl_cache import CustomTelegramClient
from ..types import HerokuReplyMarkup, ListLike, Module

FormattingEntity = typing.Union[
    MessageEntityUnknown,
    MessageEntityMention,
    MessageEntityHashtag,
    MessageEntityBotCommand,
    MessageEntityUrl,
    MessageEntityEmail,
    MessageEntityBold,
    MessageEntityItalic,
    MessageEntityCode,
    MessageEntityPre,
    MessageEntityTextUrl,
    MessageEntityMentionName,
    MessageEntityPhone,
    MessageEntityCashtag,
    MessageEntityUnderline,
    MessageEntityStrike,
    MessageEntityBlockquote,
    MessageEntityBankCard,
    MessageEntitySpoiler,
]

emoji_pattern = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport & map symbols
    "\U0001f1e0-\U0001f1ff"  # flags (iOS)
    "]+",
    flags=re.UNICODE,
)

parser = herokutl.utils.sanitize_parse_mode("html")
logger = logging.getLogger(__name__)

def get_version_raw() -> str:
    """
    Get the version of the userbot
    :return: Version in format %s.%s.%s
    """
    from .. import version

    return ".".join(map(str, list(version.__version__)))


def get_base_dir() -> str:
    """
    Get directory of this file
    :return: Directory of this file
    """
    return get_dir(__file__)


def get_dir(mod: str) -> str:
    """
    Get directory of given module
    :param mod: Module's `__file__` to get directory of
    :return: Directory of given module
    """
    return(os.getcwd() + "/heroku")
