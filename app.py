from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from bot import prepare_all
from bot.config import API_TOKEN

if not API_TOKEN:
    raise SystemExit('API_TOKEN environment variable is not set')

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot=bot, storage=storage)


async def on_startup(_) -> None:
    await prepare_all(dp)


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           skip_updates=True,
                           on_startup=on_startup)
