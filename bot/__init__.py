from aiogram import Dispatcher

from bot.commands import set_commands
from bot.handlers import register_handlers
from bot.handlers.hiding import hide_all
from bot.sql import start_db


async def prepare_all(dp: Dispatcher) -> None:
    await start_db()
    await register_handlers(dp)
    await set_commands(dp.bot)


async def shutdown_all(dp: Dispatcher) -> None:
    # Timers are kept in memory, so hide every shown number before stopping
    await hide_all(dp.bot)
