# ©️ Codrago, 2024-2030
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

# scope: no_ml

import asyncio
import logging

from dataclasses import dataclass

from aiogram.types import InputPollOption, Message as AiogramMessage, PollAnswer

from .. import loader
from ..inline.types import BotInlineCall
from ..types import Message

logger = logging.getLogger(__name__)

ANS_COUNT = 4


@dataclass()
class PollStep:
    key: str
    answer_index: int

    @property
    def answer_keys(self):
        return [f"{self.key}_ans{i + 1}" for i in range(ANS_COUNT)]

    @property
    def hint(self):
        return f"{self.key}_hint"

    def is_correct(self, index: int):
        return self.answer_index == index


@dataclass()
class PollStatus:
    poll_id: str
    message_ids: list[int]
    answers: list[bool]
    step: int


QUESTIONS = [
    PollStep("q1", 3),
    PollStep("q2", 1),
    PollStep("q3", 2),
    PollStep("q4", 3),
]


@loader.tds
class LoaderRestrictor(loader.Module):
    strings = {"name": "LoaderRestrictor"}

    async def client_ready(self):
        self.poll: PollStatus | None = None
        self.inline._dp.poll_answer.register(self.poll_handler)

        if not self.get("passed", False):
            await self.inline.bot.send_message(
                self.client.tg_id,
                self.strings["unlock_prompt"],
                reply_markup=self.inline.generate_markup(
                    [
                        [
                            {
                                "text": self.strings["unlock_prompt_btn"],
                                "callback": self._unlock_prompt_callback,
                            }
                        ]
                    ]
                ),
            )

    async def _unlock_prompt_callback(self, call: BotInlineCall):
        await call.delete()
        await self._start_quiz()

    async def _send_poll(self, poll_step: PollStep) -> AiogramMessage:
        return await self.inline.bot.send_poll(
            self.client.tg_id,
            question=self.strings[poll_step.key],
            options=[
                InputPollOption(text=self.strings[ans])
                for ans in poll_step.answer_keys
            ],
            type="quiz",
            is_anonymous=False,
            correct_option_id=poll_step.answer_index,
            explanation=self.strings[poll_step.hint],
        )

    async def poll_handler(self, poll_answer: PollAnswer):
        if self.get("passed", False):
            return

        if not self.poll or poll_answer.poll_id != self.poll.poll_id:
            return

        if poll_answer.user is None or poll_answer.user.id != self.client.tg_id:
            return

        if not poll_answer.option_ids:
            return

        correct = QUESTIONS[self.poll.step].is_correct(poll_answer.option_ids[0])
        self.poll.answers.append(correct)

        if not correct:
            return await self._abort_quiz("failed")

        await self._next_step_quiz()

    async def _watch_timeout(self, poll_id: str):
        await asyncio.sleep(60)
        if self.poll and self.poll.poll_id == poll_id:
            await self._abort_quiz("timeout")

    async def _start_quiz(self):
        if self.get("passed", False):
            await self.inline.bot.send_message(
                self.client.tg_id,
                self.strings["already_passed"],
            )
            return

        if self.poll:
            await self.inline.bot.delete_messages(
                self.client.tg_id, self.poll.message_ids
            )

        step = QUESTIONS[0]
        poll_m = await self._send_poll(step)

        self.poll = PollStatus(
            poll_id=poll_m.poll.id,
            message_ids=[poll_m.message_id],
            answers=[],
            step=0,
        )
        asyncio.create_task(self._watch_timeout(self.poll.poll_id))

    async def _next_step_quiz(self):
        if self.poll.step == len(QUESTIONS) - 1:
            return await self._end_quiz()

        self.poll.step += 1
        question = QUESTIONS[self.poll.step]

        poll_m = await self._send_poll(question)
        self.poll.message_ids.append(poll_m.message_id)
        self.poll.poll_id = poll_m.poll.id
        asyncio.create_task(self._watch_timeout(self.poll.poll_id))

    async def _end_quiz(self):
        message_ids = self.poll.message_ids
        self.poll = None
        self.set("passed", True)

        await self.inline.bot.delete_messages(self.client.tg_id, message_ids)
        await self.inline.bot.send_message(
            self.client.tg_id,
            self.strings["unlocked"],
        )

    async def _abort_quiz(self, message_key: str):
        self.poll = None
        await self.inline.bot.send_message(
            self.client.tg_id,
            self.strings[message_key],
        )

    async def aiogram_watcher(self, message: AiogramMessage):
        if (
            message.text != "/start lm_verify"
            or message.from_user is None
            or message.from_user.id != self.client.tg_id
        ):
            return

        await message.delete()

        await self._start_quiz()

    @loader.command()
    async def testquiz(self, message: Message):
        await message.delete()
        await self._start_quiz()
