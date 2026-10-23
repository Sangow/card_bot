import logging
from contextlib import suppress
from datetime import datetime, timezone
from time import monotonic

from aiogram import Bot
from aiogram.types import Update

from bot.config import ADMIN_CHAT_ID, STARTUP_ALERT
from bot.texts import t, get_lang

logger = logging.getLogger(__name__)

# The same error is reported at most once in this many seconds
ALERT_INTERVAL = 600
# Alerts are for the bot's owner, who reads Ukrainian
ALERT_LANG = 'uk'

# Error description -> (when it was last reported, times it repeated since)
alerts = {}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime('%d.%m %H:%M')


def describe(exception: Exception) -> str:
    # Only the type and message: never what the user sent
    return f'{type(exception).__name__}: {exception}'[:300]


def action_of(update: Update) -> str:
    if update.callback_query:
        return t(ALERT_LANG, 'alert_action_button')
    if update.message:
        return t(ALERT_LANG, 'alert_action_message')

    return t(ALERT_LANG, 'alert_action_other')


async def notify_admin(update: Update, exception: Exception) -> None:
    if ADMIN_CHAT_ID is None:
        return

    error = describe(exception)
    now = monotonic()
    reported_at, repeats = alerts.get(error, (None, 0))

    if reported_at is not None and now - reported_at < ALERT_INTERVAL:
        alerts[error] = (reported_at, repeats + 1)
        return

    alerts[error] = (now, 0)

    text = t(ALERT_LANG, 'alert', error=error, action=action_of(update),
             time=now_utc())
    if repeats:
        text += '\n' + t(ALERT_LANG, 'alert_repeats', count=repeats)

    # A broken alert must not hide the error it reports
    try:
        await Bot.get_current().send_message(chat_id=ADMIN_CHAT_ID, text=text)
    except Exception:
        logger.exception('Failed to send error alert')


async def notify_startup(bot: Bot) -> None:
    if ADMIN_CHAT_ID is None or not STARTUP_ALERT:
        return

    # The bot must start even if the alert cannot be sent
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID,
                               text=t(ALERT_LANG, 'startup_alert',
                                      time=now_utc()))
    except Exception:
        logger.exception('Failed to send startup alert')


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

    await notify_admin(update, exception)

    return True
