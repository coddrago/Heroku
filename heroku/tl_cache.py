# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

# ©️ Codrago, 2024-2030
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import copy
import inspect
import logging
import sys
import time
import typing

from pathlib import Path

import pyrogram
from pyrogram.client import Client as TelegramClient
# from herokutl.client import TelegramClient
from pyrogram import __name__ as __base_name__, errors, types
# from pyrogram._updates import ChannelState, Entity, EntityType, SessionState
from pyrogram.errors import RPCError
from pyrogram.errors import TopicDeleted
from pyrogram.types import User, Chat
from pyrogram.raw import functions
from pyrogram.raw.all import layer as LAYER
from pyrogram.raw.functions.channels import GetFullChannel
from pyrogram.raw.functions.users import GetFullUser
# from pyrogram.tl.tlobject import TLRequest
from pyrogram.raw.types import (
    ChannelFull,
    Message,
    Updates,
    UpdatesCombined,
    UpdateShort,
    UserFull,
)
# from pyrogram.utils import is_list_like

from .types import (
    CacheRecordEntity,
    CacheRecordFullChannel,
    CacheRecordFullUser,
    CacheRecordPerms,
    Module,
)

if typing.TYPE_CHECKING:
    from .types import EntityLike
    from .database import Database
    from .dispatcher import CommandDispatcher
    from .loader import Modules
    from .inline.core import InlineManager

logger = logging.getLogger(__name__)


def hashable(value: typing.Any) -> bool:
    """
    Determine whether `value` can be hashed.

    This is a copy of `collections.abc.Hashable` from Python 3.8.
    """

    try:
        hash(value)
    except TypeError:
        return False

    return True

def get_running_loop():
    if sys.version_info >= (3, 7):
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.get_event_loop_policy().get_event_loop()
    else:
        return asyncio.get_event_loop()


class CustomClient(TelegramClient): # TODO: rewrite the cache specially for Kurigram
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._heroku_entity_cache: typing.Dict[
            typing.Union[str, int],
            CacheRecordEntity,
        ] = {}

        self._heroku_perms_cache: typing.Dict[
            typing.Union[str, int],
            CacheRecordPerms,
        ] = {}

        self._heroku_fullchannel_cache: typing.Dict[
            typing.Union[str, int],
            CacheRecordFullChannel,
        ] = {}

        self._heroku_fulluser_cache: typing.Dict[
            typing.Union[str, int],
            CacheRecordFullUser,
        ] = {}

        self._forbidden_constructors: typing.List[int] = []

        self._raw_updates_processor: typing.Optional[
            typing.Callable[
                [typing.Union[Updates, UpdatesCombined, UpdateShort]],
                typing.Any,
            ]
        ] = None
        self._heroku_dispatcher: "CommandDispatcher"
        self.tg_id: int
        self._tg_id: int
        self.heroku_me: "User"
        self.hikka_me: "User"
        self.heroku_db: "Database"
        self.loader: "Modules"
        self.heroku_inline: "InlineManager"

    def _export_init_kwargs(self) -> dict:
        return {
            "api_id": self.api_id,
            "api_hash": self.api_hash,
            "app_version": self.app_version,
            "device_model": self.device_model,
            "system_version": self.system_version,
            "workdir": self.workdir,
            "lang_code": self.lang_code,
            "system_lang_code": self.system_lang_code,
            "proxy": self.proxy,
        }

    # async def connect(self, unix_socket_path: typing.Optional[str] = None):
    #     if self.session is None:
    #         raise ValueError(
    #             "TelegramClient instance cannot be reused after logging out"
    #         )

    #     if self._loop is None:
    #         self._loop = get_running_loop()
    #     elif self._loop != get_running_loop():
    #         raise RuntimeError(
    #             "The asyncio event loop must not change after connection (see the FAQ"
    #             " for details)"
    #         )

    #     if self._catch_up:
    #         ss = SessionState(0, 0, False, 0, 0, 0, 0, None)
    #         cs = []

    #         for entity_id, state in self.session.get_update_states():
    #             if entity_id == 0:
    #                 # TODO current session doesn't store self-user info but adding that is breaking on downstream session impls
    #                 ss = SessionState(
    #                     0,
    #                     0,
    #                     False,
    #                     state.pts,
    #                     state.qts,
    #                     int(state.date.timestamp()),
    #                     state.seq,
    #                     None,
    #                 )
    #             else:
    #                 cs.append(ChannelState(entity_id, state.pts))

    #         self._message_box.load(ss, cs)
    #         for state in cs:
    #             try:
    #                 entity = self.session.get_input_entity(state.channel_id)
    #             except ValueError:
    #                 self._log[__name__].warning(
    #                     "No access_hash in cache for channel %s, will not catch up",
    #                     state.channel_id,
    #                 )
    #             else:
    #                 self._mb_entity_cache.put(
    #                     Entity(
    #                         EntityType.CHANNEL, entity.channel_id, entity.access_hash
    #                     )
    #                 )

    #     self._init_request.query = functions.help.GetConfig()

    #     req = self._init_request
    #     if self._no_updates:
    #         req = functions.InvokeWithoutUpdates(req)

    #     await self._sender.send(functions.InvokeWithLayer(LAYER, req))

    #     if self._message_box.is_empty():
    #         me = await self.get_me()
    #         if me:
    #             await self._on_login(
    #                 me
    #             )  # also calls GetState to initialize the MessageBox

    #     self._updates_handle = self.loop.create_task(self._update_loop())
    #     self._keepalive_handle = self.loop.create_task(self._keepalive_loop())

    @property
    def raw_updates_processor(self) -> typing.Optional[callable]:
        return self._raw_updates_processor

    @raw_updates_processor.setter
    def raw_updates_processor(self, value: callable):
        if self._raw_updates_processor is not None:
            raise ValueError("raw_updates_processor is already set")

        if not callable(value):
            raise ValueError("raw_updates_processor must be callable")

        self._raw_updates_processor = value

    @property
    def heroku_entity_cache(self) -> typing.Dict[int, CacheRecordEntity]:
        return self._heroku_entity_cache

    @property
    def heroku_perms_cache(self) -> typing.Dict[int, CacheRecordPerms]:
        return self._heroku_perms_cache

    @property
    def heroku_fullchannel_cache(self) -> typing.Dict[int, CacheRecordFullChannel]:
        return self._heroku_fullchannel_cache

    @property
    def heroku_fulluser_cache(self) -> typing.Dict[int, CacheRecordFullUser]:
        return self._heroku_fulluser_cache

    @property
    def forbidden_constructors(self) -> typing.List[str]:
        return self._forbidden_constructors

    async def force_get_entity(self, *args, **kwargs):
        """Forcefully makes a request to Telegram to get the entity."""

        return await self.get_entity(*args, force=True, **kwargs)

    async def get_chat(
        self,
        chat_id: int | str,
        force_full: bool = False,
        force_fetch: bool = False
    ) -> "Chat":
        """Get information about a chat.

        Information include current name of the user for one-on-one conversations, current username of a user, group or
        channel, etc.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                Unique identifier for the target chat in form of a *t.me/joinchat/* link, identifier (int) or username
                of the target channel/supergroup (in the format @username).

            force_full (``bool``, *optional*):
                Pass True, if you need to fetch full chat information.
                Defaults to False.
            
            force_fetch (``bool``, *optional*):
                Pass True, if you need to exactly fetch up to date information about a chat.
                Defaults to False.

        Returns:
            :obj:`~pyrogram.types.Chat`: On success, if you've already joined the chat, a chat object is returned,
            otherwise, a chat preview object is returned.

        Raises:
            ValueError: In case the chat invite link points to a chat you haven't joined yet.

        Example:
            .. code-block:: python

                chat = await app.get_chat("pyrogram")
                print(chat)
        """
        if force_fetch:
            return await super().get_chat(chat_id=chat_id, force_full=force_full)

        return await self.get_entity(chat_id)

    async def get_entity(
        self,
        entity: int | str,
        exp: int = 5 * 60,
        force: bool = False,
    ) -> "Chat":
        """
        Gets the entity and cache it

        :param entity: Entity to fetch
        :param exp: Expiration time of the cache record and maximum time of already cached record
        :param force: Whether to force refresh the cache (make API request)
        :return: :obj:`Entity`
        """

        # Will be used to determine, which client caused logging messages
        # parsed via inspect.stack()
        _heroku_client_id_logging_tag = copy.copy(self.tg_id)  # noqa: F841

        if not hashable(entity):
            try:
                hashable_entity = next(
                    getattr(entity, attr)
                    for attr in {"user_id", "channel_id", "chat_id", "id"}
                    if getattr(entity, attr, None)
                )
            except StopIteration:
                logger.debug(
                    "Can't parse hashable from entity %s, using legacy resolve",
                    entity,
                )
                return await self.get_chat(entity, force_full=force, force_fetch=True)
        else:
            hashable_entity = entity

        if str(hashable_entity).startswith("-100"):
            hashable_entity = int(str(hashable_entity)[4:])

        if (
            not force
            and hashable_entity
            and hashable_entity in self._heroku_entity_cache
            and (
                not exp
                or self._heroku_entity_cache[hashable_entity].ts + exp > time.time()
            )
        ):
            logger.debug(
                "Using cached entity %s (%s)",
                entity,
                type(self._heroku_entity_cache[hashable_entity].entity).__name__,
            )
            return copy.deepcopy(self._heroku_entity_cache[hashable_entity].entity)

        resolved_entity = await self.get_chat(entity, force_full=force, force_fetch=True)

        if resolved_entity:
            cache_record = CacheRecordEntity(hashable_entity, resolved_entity, exp)
            self._heroku_entity_cache[hashable_entity] = cache_record
            logger.debug("Saved hashable_entity %s to cache", hashable_entity)

            if getattr(resolved_entity, "id", None):
                logger.debug("Saved resolved_entity id %s to cache", resolved_entity.id)
                self._heroku_entity_cache[resolved_entity.id] = cache_record

            if getattr(resolved_entity, "username", None):
                logger.debug(
                    "Saved resolved_entity username @%s to cache",
                    resolved_entity.username,
                )
                self._heroku_entity_cache[f"@{resolved_entity.username}"] = cache_record
                self._heroku_entity_cache[resolved_entity.username] = cache_record

        return copy.deepcopy(resolved_entity)

    # async def get_perms_cached(
    #     self,
    #     entity: 'EntityLike',
    #     user: typing.Optional['EntityLike'] = None,
    #     exp: int = 5 * 60,
    #     force: bool = False,
    # ):
    #     """
    #     Gets the permissions of the user in the entity and cache it

    #     :param entity: Entity to fetch
    #     :param user: User to fetch
    #     :param exp: Expiration time of the cache record and maximum time of already cached record
    #     :param force: Whether to force refresh the cache (make API request)
    #     :return: :obj:`ChatPermissions`
    #     """

    #     # Will be used to determine, which client caused logging messages
    #     # parsed via inspect.stack()
    #     _heroku_client_id_logging_tag = copy.copy(self.tg_id)  # noqa: F841

    #     entity = await self.get_entity(entity)
    #     user = await self.get_entity(user) if user else None

    #     if not hashable(entity) or not hashable(user):
    #         try:
    #             hashable_entity = next(
    #                 getattr(entity, attr)
    #                 for attr in {"user_id", "channel_id", "chat_id", "id"}
    #                 if getattr(entity, attr, None)
    #             )
    #         except StopIteration:
    #             logger.debug(
    #                 "Can't parse hashable from entity %s, using legacy method",
    #                 entity,
    #             )
    #             return await self.get_permissions(entity, user)

    #         try:
    #             hashable_user = next(
    #                 getattr(user, attr)
    #                 for attr in {"user_id", "channel_id", "chat_id", "id"}
    #                 if getattr(user, attr, None)
    #             )
    #         except StopIteration:
    #             logger.debug(
    #                 "Can't parse hashable from user %s, using legacy method",
    #                 user,
    #             )
    #             return await self.get_permissions(entity, user)
    #     else:
    #         hashable_entity = entity
    #         hashable_user = user

    #     if str(hashable_entity).isdigit() and int(hashable_entity) < 0:
    #         hashable_entity = int(str(hashable_entity)[4:])

    #     if str(hashable_user).isdigit() and int(hashable_user) < 0:
    #         hashable_user = int(str(hashable_user)[4:])

    #     if (
    #         not force
    #         and hashable_entity
    #         and hashable_user
    #         and hashable_user in self._heroku_perms_cache.get(hashable_entity, {})
    #         and (
    #             not exp
    #             or self._heroku_perms_cache[hashable_entity][hashable_user].ts + exp
    #             > time.time()
    #         )
    #     ):
    #         logger.debug("Using cached perms %s (%s)", hashable_entity, hashable_user)
    #         return copy.deepcopy(
    #             self._heroku_perms_cache[hashable_entity][hashable_user].perms
    #         )

    #     resolved_perms = await self.get_permissions(entity, user)

    #     if resolved_perms:
    #         cache_record = CacheRecordPerms(
    #             hashable_entity,
    #             hashable_user,
    #             resolved_perms,
    #             exp,
    #         )
    #         self._heroku_perms_cache.setdefault(hashable_entity, {})[hashable_user] = (
    #             cache_record
    #         )
    #         logger.debug("Saved hashable_entity %s perms to cache", hashable_entity)

    #         def save_user(key: typing.Union[str, int]):
    #             nonlocal self, cache_record, user, hashable_user
    #             if getattr(user, "id", None):
    #                 self._heroku_perms_cache.setdefault(key, {})[user.id] = cache_record

    #             if getattr(user, "username", None):
    #                 self._heroku_perms_cache.setdefault(key, {})[f"@{user.username}"] = (
    #                     cache_record
    #                 )
    #                 self._heroku_perms_cache.setdefault(key, {})[user.username] = (
    #                     cache_record
    #                 )

    #         if getattr(entity, "id", None):
    #             logger.debug("Saved resolved_entity id %s perms to cache", entity.id)
    #             save_user(entity.id)

    #         if getattr(entity, "username", None):
    #             logger.debug(
    #                 "Saved resolved_entity username @%s perms to cache",
    #                 entity.username,
    #             )
    #             save_user(f"@{entity.username}")
    #             save_user(entity.username)

    #     return copy.deepcopy(resolved_perms)

    # async def get_fullchannel(
    #     self,
    #     entity: 'EntityLike',
    #     exp: int = 300,
    #     force: bool = False,
    # ) -> ChannelFull:
    #     """
    #     Gets the FullChannel and cache it

    #     :param entity: Channel to fetch ChannelFull of
    #     :param exp: Expiration time of the cache record and maximum time of already cached record
    #     :param force: Whether to force refresh the cache (make API request)
    #     :return: :obj:`ChannelFull`
    #     """
    #     if not hashable(entity):
    #         try:
    #             hashable_entity = next(
    #                 getattr(entity, attr)
    #                 for attr in {"channel_id", "chat_id", "id"}
    #                 if getattr(entity, attr, None)
    #             )
    #         except StopIteration:
    #             logger.debug(
    #                 (
    #                     "Can't parse hashable from entity %s, using legacy fullchannel"
    #                     " request"
    #                 ),
    #                 entity,
    #             )
    #             return await self(GetFullChannel(channel=entity))
    #     else:
    #         hashable_entity = entity

    #     if str(hashable_entity).isdigit() and int(hashable_entity) < 0:
    #         hashable_entity = int(str(hashable_entity)[4:])

    #     if (
    #         not force
    #         and self._heroku_fullchannel_cache.get(hashable_entity)
    #         and not self._heroku_fullchannel_cache[hashable_entity].expired
    #         and self._heroku_fullchannel_cache[hashable_entity].ts + exp > time.time()
    #     ):
    #         return self._heroku_fullchannel_cache[hashable_entity].full_channel

    #     result = await self(GetFullChannel(channel=entity))
    #     self._heroku_fullchannel_cache[hashable_entity] = CacheRecordFullChannel(
    #         hashable_entity,
    #         result,
    #         exp,
    #     )
    #     return result

    # async def get_fulluser(
    #     self,
    #     entity: 'EntityLike',
    #     exp: int = 300,
    #     force: bool = False,
    # ) -> UserFull:
    #     """
    #     Gets the FullUser and cache it

    #     :param entity: User to fetch UserFull of
    #     :param exp: Expiration time of the cache record and maximum time of already cached record
    #     :param force: Whether to force refresh the cache (make API request)
    #     :return: :obj:`UserFull`
    #     """
    #     if not hashable(entity):
    #         try:
    #             hashable_entity = next(
    #                 getattr(entity, attr)
    #                 for attr in {"user_id", "chat_id", "id"}
    #                 if getattr(entity, attr, None)
    #             )
    #         except StopIteration:
    #             logger.debug(
    #                 (
    #                     "Can't parse hashable from entity %s, using legacy fulluser"
    #                     " request"
    #                 ),
    #                 entity,
    #             )
    #             return await self(GetFullUser(entity))
    #     else:
    #         hashable_entity = entity

    #     if str(hashable_entity).isdigit() and int(hashable_entity) < 0:
    #         hashable_entity = int(str(hashable_entity)[4:])

    #     if (
    #         not force
    #         and self._heroku_fulluser_cache.get(hashable_entity)
    #         and not self._heroku_fulluser_cache[hashable_entity].expired
    #         and self._heroku_fulluser_cache[hashable_entity].ts + exp > time.time()
    #     ):
    #         return self._heroku_fulluser_cache[hashable_entity].full_user

    #     result = await self(GetFullUser(entity))
    #     self._heroku_fulluser_cache[hashable_entity] = CacheRecordFullUser(
    #         hashable_entity,
    #         result,
    #         exp,
    #     )
    #     return result

    # @staticmethod
    # def _find_message_obj_in_frame(
    #     chat_id: int,
    #     frame: inspect.FrameInfo,
    # ) -> typing.Optional[Message]:
    #     """
    #     Finds the message object from the frame
    #     """
    #     logger.debug("Finding message object in frame %s", frame)
    #     return next(
    #         (
    #             obj
    #             for obj in frame.frame.f_locals.values()
    #             if isinstance(obj, Message)
    #             and getattr(obj.reply_to, "forum_topic", False)
    #             and chat_id == getattr(obj.peer_id, "channel_id", None)
    #         ),
    #         None,
    #     )

    # async def _find_message_obj_in_stack(
    #     self,
    #     chat: 'EntityLike',
    #     stack: typing.List[inspect.FrameInfo],
    # ) -> typing.Optional[Message]:
    #     """
    #     Finds the message object from the stack
    #     """
    #     chat_id = (await self.get_entity(chat, exp=0)).id
    #     logger.debug("Finding message object in stack for chat %s", chat_id)
    #     return next(
    #         (
    #             self._find_message_obj_in_frame(chat_id, frame_info)
    #             for frame_info in stack
    #             if self._find_message_obj_in_frame(chat_id, frame_info)
    #         ),
    #         None,
    #     )

    # async def _find_topic_in_stack(
    #     self,
    #     chat: 'EntityLike',
    #     stack: typing.List[inspect.FrameInfo],
    # ) -> typing.Optional[Message]:
    #     """
    #     Finds the message object from the stack
    #     """
    #     message = await self._find_message_obj_in_stack(chat, stack)
    #     return (
    #         (message.reply_to.reply_to_top_id or message.reply_to.reply_to_msg_id)
    #         if message
    #         else None
    #     )

    # async def _topic_guesser(
    #     self,
    #     native_method: typing.Callable[..., typing.Awaitable[Message]],
    #     stack: typing.List[inspect.FrameInfo],
    #     *args,
    #     **kwargs,
    # ):
    #     no_retry = kwargs.pop("_topic_no_retry", False)
    #     try:
    #         return await native_method(*args, **kwargs)
    #     except TopicDeleted:
    #         if no_retry:
    #             raise

    #         logger.debug("Topic deleted, trying to guess topic id")

    #         topic = await self._find_topic_in_stack(args[0], stack)

    #         logger.debug("Guessed topic id: %s", topic)

    #         if not topic:
    #             raise

    #         kwargs["reply_to"] = topic
    #         kwargs["_topic_no_retry"] = True
    #         return await self._topic_guesser(native_method, stack, *args, **kwargs)

    # async def send_document(self, *args, **kwargs) -> Message:
    #     return await self._topic_guesser(
    #         super().send_document,
    #         inspect.stack(),
    #         *args,
    #         **kwargs,
    #     )

    # async def send_message(self, *args, **kwargs) -> Message:
    #     return await self._topic_guesser(
    #         super().send_message,
    #         inspect.stack(),
    #         *args,
    #         **kwargs,
    #     )

    async def promote_chat_member(
        self: "pyrogram.Client",
        chat_id: int | str,
        user_id: int | str,
        privileges: "types.ChatAdministratorRights" = None,
        title: str = None
    ) -> bool:
        """Promote or demote a user in a supergroup or a channel.

        You must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Pass False for all boolean parameters to demote a user.

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.

            user_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target user.
                For a contact that exists in your Telegram address book you can use his phone number (str).

            privileges (:obj:`~pyrogram.types.ChatAdministratorRights`, *optional*):
                New user privileges.
            
            title (``str``, *optional*):
                A custom title that will be shown to all members instead of "Owner" or "Admin".
                Pass None or "" (empty string) to remove the custom title.

        Returns:
            ``bool``: True on success.

        Example:
            .. code-block:: python

                # Promote chat member to admin
                await app.promote_chat_member(chat_id, user_id)
        """
        chat_id = await self.resolve_peer(chat_id)
        user_id = await self.resolve_peer(user_id)

        # See Chat.promote_member for the reason of this (instead of setting types.ChatAdministratorRights() as default arg).
        if privileges is None:
            privileges = types.ChatAdministratorRights()

        try:
            raw_chat_member = (await self.invoke(
                functions.channels.GetParticipant(
                    channel=chat_id,
                    participant=user_id
                )
            )).participant
        except errors.RPCError:
            raw_chat_member = None

        rank = title
        if not rank and isinstance(raw_chat_member, pyrogram.raw.types.ChannelParticipantAdmin):
            rank = raw_chat_member.rank

        await self.invoke(
            functions.channels.EditAdmin(
                channel=chat_id,
                user_id=user_id,
                admin_rights=pyrogram.raw.types.ChatAdminRights(
                    anonymous=privileges.is_anonymous,
                    change_info=privileges.can_change_info,
                    post_messages=privileges.can_post_messages,
                    post_stories=privileges.can_post_stories,
                    edit_messages=privileges.can_edit_messages,
                    edit_stories=privileges.can_edit_stories,
                    delete_messages=privileges.can_delete_messages,
                    delete_stories=privileges.can_delete_stories,
                    ban_users=privileges.can_restrict_members,
                    invite_users=privileges.can_invite_users,
                    pin_messages=privileges.can_pin_messages,
                    add_admins=privileges.can_promote_members,
                    manage_call=privileges.can_manage_video_chats,
                    manage_topics=privileges.can_manage_topics,
                    other=privileges.can_manage_chat
                ),
                rank=rank or ""
            )
        )

        return True

    # async def _call(
    #     self,
    #     sender: MTProtoSender,
    #     request: TLRequest,
    #     ordered: bool = False,
    #     flood_sleep_threshold: typing.Optional[int] = None,
    # ):
    #     """
    #     Calls the given request and handles user-side forbidden constructors

    #     :param sender: Sender to use
    #     :param request: Request to send
    #     :param ordered: Whether to send the request ordered
    #     :param flood_sleep_threshold: Flood sleep threshold
    #     :return: The result of the request
    #     """

    #     # ⚠️⚠️  WARNING!  ⚠️⚠️
    #     # If you are a module developer, and you'll try to bypass this protection to
    #     # force user join your channel, you will be added to SCAM modules
    #     # list and you will be banned from Heroku federation.
    #     # Let USER decide, which channel he will follow. Do not be so petty
    #     # I hope, you understood me.
    #     # Thank you

    #     not_tuple = False
    #     if not is_list_like(request):
    #         not_tuple = True
    #         request = (request,)

    #     new_request = []

    #     for item in request:
    #         if item.CONSTRUCTOR_ID in self._forbidden_constructors and next(
    #             (
    #                 frame_info.frame.f_locals["self"]
    #                 for frame_info in inspect.stack()
    #                 if hasattr(frame_info, "frame")
    #                 and hasattr(frame_info.frame, "f_locals")
    #                 and isinstance(frame_info.frame.f_locals, dict)
    #                 and "self" in frame_info.frame.f_locals
    #                 and isinstance(frame_info.frame.f_locals["self"], Module)
    #                 and not getattr(
    #                     frame_info.frame.f_locals["self"], "__origin__", ""
    #                 ).startswith("<core")
    #             ),
    #             None,
    #         ):
    #             logger.debug(
    #                 "🎉 I protected you from unintented %s (%s)!",
    #                 item.__class__.__name__,
    #                 item,
    #             )
    #             continue

    #         new_request += [item]

    #     if not new_request:
    #         return

    #     return await super()._call(
    #         sender,
    #         new_request[0] if not_tuple else tuple(new_request),
    #         ordered,
    #         flood_sleep_threshold,
    #     )

    # def _internal_forbid_ctor(self, constructors: list):
    #     self._forbidden_constructors.extend(constructors)
    #     self._forbidden_constructors = list(set(self._forbidden_constructors))

    # def forbid_constructor(self, constructor: int):
    #     """
    #     Forbids the given constructor to be called

    #     :param constructor: Constructor id to forbid
    #     """
    #     self._internal_forbid_ctor([constructor])

    # def forbid_constructors(self, constructors: list):
    #     """
    #     Forbids the given constructors to be called.

    #     :param constructors: Constructor ids to forbid
    #     """
    #     self._internal_forbid_ctor(constructors)

    # def _handle_update(
    #     self: "CustomTelegramClient",
    #     update: typing.Union[Updates, UpdatesCombined, UpdateShort],
    # ):
    #     if self._raw_updates_processor is not None:
    #         self._raw_updates_processor(update)

    #     super()._handle_update(update)
