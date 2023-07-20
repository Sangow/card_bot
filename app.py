from os import getenv

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from bot import prepare_all

storage = MemoryStorage()
bot = Bot(token=getenv(key='API_TOKEN'))
dp = Dispatcher(bot=bot, storage=storage)


async def on_startup(_) -> None:
    await prepare_all(dp)


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           skip_updates=True,
                           on_startup=on_startup)
