from collections import deque
from contextlib import suppress
from time import monotonic

from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import CallbackQuery, InlineQuery, Message, User
from aiogram.utils.exceptions import TelegramAPIError

from bot.texts import t, get_lang
from .service import contains_card_number

# At most this many updates from one user in RATE_PERIOD seconds; a person
# tapping and typing fast stays well below it
RATE_LIMIT = 20
RATE_PERIOD = 10
# Of those, at most this many messages: each one may get a reply, and
# Telegram allows a bot about one message a second in a chat
MESSAGE_LIMIT = 10
# A user who goes over the limit this many times in BURST_WINDOW seconds is
# ignored for a while, so the bursts cannot be repeated without end
MUTE_AFTER_BURSTS = 3
BURST_WINDOW = 600
# How long each next mute lasts; past the last one, mutes stay that long
MUTE_DURATIONS = (600, 3600)
# After this long without a mute, the next one is the shortest again
MUTE_RESET = 86400
# Past this many users, the ones who have gone quiet are forgotten, so the
# counters do not grow with every user the bot has ever seen
MAX_TRACKED_USERS = 1000

# What to do with an update
ALLOW = 'allow'
# Ignore it and tell the user to slow down
WARN = 'warn'
# Ignore it and tell the user they are muted
MUTE = 'mute'
# Ignore it silently
IGNORE = 'ignore'


class UserLimit:
    """What is known about how fast one user sends updates."""

    def __init__(self):
        # Times of recent updates, and of the messages among them
        self.updates = deque()
        self.messages = deque()
        # Whether the user was told to slow down in their current burst
        self.warned = False
        # Times of the user's recent bursts over the limit
        self.bursts = deque()
        # When the last mute ends, and how long it is
        self.muted_until = None
        self.mute_length = 0
        # Mutes in a row; each next one is longer
        self.mutes = 0

    def muted(self, now: float) -> bool:
        return self.muted_until is not None and now < self.muted_until

    def quiet(self, now: float) -> bool:
        """Nothing worth remembering: no recent updates, bursts or mutes."""
        return (not self.updates or now - self.updates[-1] >= RATE_PERIOD) \
            and (not self.bursts or now - self.bursts[-1] >= BURST_WINDOW) \
            and (self.muted_until is None
                 or now - self.muted_until >= MUTE_RESET)

    def mute(self, now: float) -> None:
        if self.muted_until is not None and \
                now - self.muted_until >= MUTE_RESET:
            self.mutes = 0

        self.mute_length = MUTE_DURATIONS[min(self.mutes,
                                              len(MUTE_DURATIONS) - 1)]
        self.mutes += 1
        self.muted_until = now + self.mute_length
        self.bursts.clear()
        self.updates.clear()
        self.messages.clear()


class ThrottlingMiddleware(BaseMiddleware):
    """Ignores updates from a user who sends too many of them, so one user
    cannot use up the bot's Telegram limits for everyone."""

    def __init__(self):
        super().__init__()
        # User id -> how fast they send updates
        self.users = {}

    def forget_quiet(self, now: float) -> None:
        for user_id, user in list(self.users.items()):
            if user.quiet(now):
                del self.users[user_id]

    def check(self, user_id: int, message: bool = False) -> str:
        now = monotonic()

        if len(self.users) > MAX_TRACKED_USERS:
            self.forget_quiet(now)

        user = self.users.setdefault(user_id, UserLimit())

        if user.muted(now):
            return IGNORE

        for recent in (user.updates, user.messages):
            while recent and now - recent[0] >= RATE_PERIOD:
                recent.popleft()

        if len(user.updates) < RATE_LIMIT and \
                not (message and len(user.messages) >= MESSAGE_LIMIT):
            user.updates.append(now)
            if message:
                user.messages.append(now)
            user.warned = False
            return ALLOW

        # Only the first ignored update of a burst counts and gets an answer
        if user.warned:
            return IGNORE
        user.warned = True

        while user.bursts and now - user.bursts[0] >= BURST_WINDOW:
            user.bursts.popleft()
        user.bursts.append(now)

        if len(user.bursts) < MUTE_AFTER_BURSTS:
            return WARN

        user.mute(now)

        return MUTE

    def warning(self, user: User, verdict: str) -> str:
        lang = get_lang(user)

        if verdict == MUTE:
            minutes = self.users[user.id].mute_length // 60
            return t(lang, 'muted', minutes=minutes)

        return t(lang, 'too_many_actions')

    async def on_pre_process_message(self, message: Message,
                                     data: dict) -> None:
        user = message.from_user

        if user is None:
            return

        verdict = self.check(user.id, message=True)

        if verdict == ALLOW:
            return

        # A card number must not stay in the chat even when it is ignored
        if contains_card_number(message.text or ''):
            with suppress(TelegramAPIError):
                await message.delete()

        if verdict in (WARN, MUTE):
            with suppress(TelegramAPIError):
                await message.answer(text=self.warning(user, verdict))

        raise CancelHandler()

    async def on_pre_process_callback_query(self, call: CallbackQuery,
                                            data: dict) -> None:
        verdict = self.check(call.from_user.id)

        if verdict == ALLOW:
            return

        # Every button press is answered, or the button keeps spinning
        with suppress(TelegramAPIError):
            if verdict in (WARN, MUTE):
                await call.answer(text=self.warning(call.from_user, verdict),
                                  show_alert=True)
            else:
                await call.answer()

        raise CancelHandler()

    async def on_pre_process_inline_query(self, query: InlineQuery,
                                          data: dict) -> None:
        if self.check(query.from_user.id) != ALLOW:
            raise CancelHandler()
