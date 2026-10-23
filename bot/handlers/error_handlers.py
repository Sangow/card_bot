import logging
from contextlib import suppress

from aiogram.types import Update

from bot.texts import t, get_lang

logger = logging.getLogger(__name__)


async def errors_handler(update: Update, exception: Exception) -> bool:
    logger.error('Update %s caused error', update.update_id,
                 exc_info=exception)

    # The error may come from Telegram itself, so replying can fail too
    with suppress(Exception):
        if update.callback_query:
            lang = get_lang(update.callback_query.from_user)
            await update.callback_query.answer(text=t(lang, 'error'),
                                               show_alert=True)
        elif update.message:
            lang = get_lang(update.message.from_user)
            await update.message.answer(text=t(lang, 'error'))

    return True
