import asyncio
import logging
from html import escape

from aiogram import Bot
from aiogram.utils.exceptions import TelegramAPIError

from bot.config import HIDE_AFTER
from bot.keyboards import hidden_card_ikb
from bot.texts import t

logger = logging.getLogger(__name__)

# (chat_id, message_id) of messages that show a card number, mapped to the
# timer task and what to show once the number is hidden
pending = {}


def schedule_hide(bot: Bot, chat_id: int, message_id: int, card_id: int,
                  card_nickname: str, page: int, lang: str) -> None:
    cancel_hide(chat_id, message_id)

    key = (chat_id, message_id)
    view = (card_id, card_nickname, page, lang)
    pending[key] = (asyncio.create_task(hide_later(bot, key)), view)


def cancel_hide(chat_id: int, message_id: int) -> None:
    entry = pending.pop((chat_id, message_id), None)

    if entry:
        entry[0].cancel()


async def hide_later(bot: Bot, key: tuple) -> None:
    await asyncio.sleep(HIDE_AFTER)

    entry = pending.pop(key, None)

    if entry:
        await hide(bot, key, entry[1])


async def hide(bot: Bot, key: tuple, view: tuple) -> None:
    chat_id, message_id = key
    card_id, card_nickname, page, lang = view

    # The user may have deleted the message in the meantime
    try:
        await bot.edit_message_text(
            text=t(lang, 'card_hidden', nickname=escape(card_nickname)),
            chat_id=chat_id,
            message_id=message_id,
            parse_mode='html',
            reply_markup=hidden_card_ikb(card_id, lang, page)
        )
    except TelegramAPIError as e:
        logger.warning('Could not hide card number in message %s: %s',
                       message_id, e)


async def hide_all(bot: Bot) -> None:
    entries = list(pending.items())
    pending.clear()

    for key, (task, view) in entries:
        task.cancel()
        await hide(bot, key, view)
