from collections import deque
from contextlib import suppress
from time import monotonic

from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import CallbackQuery, InlineQuery, Message
from aiogram.utils.exceptions import TelegramAPIError

from bot.texts import t, get_lang
from .service import looks_like_card_number

# At most this many updates from one user in RATE_PERIOD seconds; a person
# tapping and typing fast stays well below it
RATE_LIMIT = 20
RATE_PERIOD = 10
# Past this many users, the ones who have gone quiet are forgotten, so the
# counters do not grow with every user the bot has ever seen
MAX_TRACKED_USERS = 1000


class ThrottlingMiddleware(BaseMiddleware):
    """Ignores updates from a user who sends too many of them, so one user
    cannot use up the bot's Telegram limits for everyone."""

    def __init__(self):
        super().__init__()
        # User id -> times of their recent updates
        self.recent = {}
        # Users already told to slow down in their current burst
        self.warned = set()

    def forget_quiet(self, now: float) -> None:
        for user_id, times in list(self.recent.items()):
            if not times or now - times[-1] >= RATE_PERIOD:
                del self.recent[user_id]
                self.warned.discard(user_id)

    def throttled(self, user_id: int) -> bool:
        now = monotonic()

        if len(self.recent) > MAX_TRACKED_USERS:
            self.forget_quiet(now)

        times = self.recent.setdefault(user_id, deque())
        while times and now - times[0] >= RATE_PERIOD:
            times.popleft()

        if len(times) >= RATE_LIMIT:
            return True

        times.append(now)
        self.warned.discard(user_id)

        return False

    def first_warning(self, user_id: int) -> bool:
        if user_id in self.warned:
            return False

        self.warned.add(user_id)

        return True

    async def on_pre_process_message(self, message: Message,
                                     data: dict) -> None:
        user = message.from_user

        if user is None or not self.throttled(user.id):
            return

        # A card number must not stay in the chat even when it is ignored
        if looks_like_card_number(message.text or ''):
            with suppress(TelegramAPIError):
                await message.delete()

        if self.first_warning(user.id):
            with suppress(TelegramAPIError):
                await message.answer(text=t(get_lang(user),
                                            'too_many_actions'))

        raise CancelHandler()

    async def on_pre_process_callback_query(self, call: CallbackQuery,
                                            data: dict) -> None:
        if not self.throttled(call.from_user.id):
            return

        # Every button press is answered, or the button keeps spinning
        with suppress(TelegramAPIError):
            if self.first_warning(call.from_user.id):
                await call.answer(text=t(get_lang(call.from_user),
                                         'too_many_actions'),
                                  show_alert=True)
            else:
                await call.answer()

        raise CancelHandler()

    async def on_pre_process_inline_query(self, query: InlineQuery,
                                          data: dict) -> None:
        if self.throttled(query.from_user.id):
            raise CancelHandler()
