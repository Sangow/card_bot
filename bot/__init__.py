from aiogram import Dispatcher

from bot.commands import set_commands
from bot.handlers import register_handlers
from bot.sql import start_db


async def prepare_all(dp: Dispatcher) -> None:
    await start_db()
    await register_handlers(dp)
    await set_commands(dp.bot)
