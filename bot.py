from os import getenv

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import Message

from keyboards import start_kb, cancel_kb, confirm_kb
from sq import start, get_cards, add_card

storage = MemoryStorage()
bot = Bot(token=getenv(key='API_TOKEN'))
dp = Dispatcher(bot=bot)


async def on_startup(_) -> None:
    global cards

    await start()


class AddCard(StatesGroup):
    card_number = State()
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


@dp.message_handler(text='ADD CARD')
async def add_card_1(message: Message) -> None:
    await message.answer(text='Enter card number:',
                         reply_markup=cancel_kb)
    await AddCard.card_number.set()


@dp.message_handler(state=AddCard.card_number)
async def add_card_2(message: Message, state: FSMContext) -> None:  # TODO validate credit card
    async with state.proxy() as data:
        data['card_number'] = message.text

    await message.answer(text=f'This is your card\n\n'
                              f'{message.text}',
                         reply_markup=confirm_kb)


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           skip_updates=True,
                           on_startup=on_startup)
