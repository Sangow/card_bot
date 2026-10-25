import asyncio
import logging

from aiohttp import ClientTimeout
from aiogram import Bot

from bot.config import HEARTBEAT_URL, HEARTBEAT_INTERVAL

logger = logging.getLogger(__name__)

# A ping that hangs must not hold up the next one
PING_TIMEOUT = ClientTimeout(total=10)

# The task that keeps pinging, while the bot runs
task = None


async def ping(bot: Bot, url: str) -> None:
    session = await bot.get_session()

    async with session.post(url, timeout=PING_TIMEOUT) as response:
        response.raise_for_status()


async def beat(bot: Bot) -> None:
    # Only a bot that reaches Telegram counts as alive, so the monitoring
    # service also alerts when Telegram cannot be reached from the server
    try:
        await bot.get_me()
        await ping(bot, HEARTBEAT_URL)
    except Exception:
        logger.warning('Heartbeat failed', exc_info=True)


async def heartbeat_loop(bot: Bot) -> None:
    while True:
        await beat(bot)
        await asyncio.sleep(HEARTBEAT_INTERVAL)


def start_heartbeat(bot: Bot) -> None:
    global task

    if HEARTBEAT_URL:
        task = asyncio.create_task(heartbeat_loop(bot))


def stop_heartbeat() -> None:
    global task

    if task:
        task.cancel()
        task = None
