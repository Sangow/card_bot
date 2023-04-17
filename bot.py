from os import getenv

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import Message

from keyboards import start_kb

storage = MemoryStorage()
bot = Bot(token=getenv(key='API_TOKEN'))
dp = Dispatcher(bot=bot)


class AddCard(StatesGroup):
    card_number = State()
    card_nickname = State()
    confirm = State()


@dp.message_handler(commands=['start'])
async def start_command(message: Message) -> None:
    await message.answer(text='This is card bot!',
                         reply_markup=start_kb)


@dp.message_handler(text='CANCEL', state='*')
async def cancel(message: Message, state: FSMContext) -> None:
    if not await state.get_state():
        return

    await state.finish()

    await message.answer(text='Cancelled.',
                         reply_markup=start_kb)


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           skip_updates=True)
