from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram.types import Message

from bot.config import ADMIN_CHAT_ID, ALERT_TIMEZONE, MAX_CARDS
from bot.keyboards import read_ikb
from bot.sql import stats
from bot.texts import t
from .error_handlers import ALERT_LANG
from .user_handlers import delete_user_message

# When this run of the bot started, shown in /stats
started_at = None


def mark_started() -> None:
    global started_at
    started_at = datetime.now(ZoneInfo(ALERT_TIMEZONE))


def is_admin(message: Message) -> bool:
    return ADMIN_CHAT_ID is not None and message.from_user.id == ADMIN_CHAT_ID


async def cmd_stats(message: Message) -> None:
    await delete_user_message(message)

    numbers = await stats()

    await message.answer(
        text=t(ALERT_LANG, 'stats', limit=MAX_CARDS,
               started=started_at.strftime('%d.%m %H:%M')
               if started_at else '—',
               **numbers),
        reply_markup=read_ikb(ALERT_LANG)
    )
