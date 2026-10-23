import logging

from aiogram import Bot
from aiogram.types import BotCommand
from aiogram.utils.exceptions import TelegramAPIError

from bot.texts import TEXTS, LANG_ALIASES, DEFAULT_LANG, t

logger = logging.getLogger(__name__)

COMMANDS = ('cards', 'add', 'cancel', 'help')


def bot_commands(lang: str) -> list:
    return [BotCommand(command=command, description=t(lang, f'cmd_{command}'))
            for command in COMMANDS]


async def set_commands(bot: Bot) -> None:
    # The menu is a convenience, so failing to set it must not stop the bot
    try:
        await bot.set_my_commands(bot_commands(DEFAULT_LANG))

        for lang in TEXTS:
            await bot.set_my_commands(bot_commands(lang), language_code=lang)

        for alias, lang in LANG_ALIASES.items():
            await bot.set_my_commands(bot_commands(lang),
                                      language_code=alias)
    except TelegramAPIError:
        logger.exception('Failed to set bot commands')


def bot_languages() -> list:
    """Language codes to set per-language texts for; None is the default."""
    return [None, *TEXTS, *LANG_ALIASES]


def text_language(language_code: str | None) -> str:
    if language_code is None:
        return DEFAULT_LANG

    return LANG_ALIASES.get(language_code, language_code)


async def set_descriptions(bot: Bot) -> None:
    # aiogram 2 has no methods for these, so the Bot API is called directly.
    # Like the menu, failing to set them must not stop the bot
    try:
        for language_code in bot_languages():
            lang = text_language(language_code)
            extra = {'language_code': language_code} if language_code else {}

            # Shown in an empty chat before the user taps Start
            await bot.request('setMyDescription', {
                'description': t(lang, 'description'), **extra})
            # Shown in the bot's profile and when its link is shared
            await bot.request('setMyShortDescription', {
                'short_description': t(lang, 'short_description'), **extra})
    except TelegramAPIError:
        logger.exception('Failed to set bot description')
