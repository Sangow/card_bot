import logging

from aiogram import Bot, Dispatcher, executor

from bot import prepare_all, shutdown_all
from bot.config import API_TOKEN, CARD_KEY, LOG_LEVEL
from bot.sql.storage import SQLiteStorage

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)

if not API_TOKEN:
    raise SystemExit('API_TOKEN environment variable is not set')
if not CARD_KEY:
    raise SystemExit('CARD_KEY environment variable is not set')

storage = SQLiteStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot=bot, storage=storage)


async def on_startup(_) -> None:
    await prepare_all(dp)


async def on_shutdown(_) -> None:
    await shutdown_all(dp)


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           # Messages sent while the bot was restarting are
                           # handled once it is up again
                           skip_updates=False,
                           on_startup=on_startup,
                           on_shutdown=on_shutdown)
