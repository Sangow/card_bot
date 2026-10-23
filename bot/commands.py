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
