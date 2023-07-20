from aiogram import Dispatcher

from bot.handlers import register_handlers
from bot.sql import start_db


async def prepare_all(dp: Dispatcher) -> None:
    await start_db()
    await register_handlers(dp)
