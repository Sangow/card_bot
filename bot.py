from os import getenv

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import Message

from keyboards import start_kb, cancel_kb, confirm_kb, nickname_kb
from sq import start, get_cards_nicknames, add_card, get_card_number

storage = MemoryStorage()
bot = Bot(token=getenv(key='API_TOKEN'))
dp = Dispatcher(bot=bot, storage=storage)


async def on_startup(_) -> None:
    global cards

    await start()


class AddCard(StatesGroup):
    card_number = State()
    card_nickname = State()
    confirm = State()


class ShowCard(StatesGroup):
    show_card_number = State()


@dp.message_handler(commands=['start'])
async def start_command(message: Message) -> None:
    await message.answer(text='This is card bot!',
                         reply_markup=start_kb)


@dp.message_handler(text='CANCEL', state='*')
async def cancel(message: Message, state: FSMContext) -> None:
    if not await state.get_state():
        await message.answer(text='Cancelled.',
                             reply_markup=start_kb)
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

    await message.answer(text='Enter card nickname:')

    await AddCard.next()


@dp.message_handler(state=AddCard.card_nickname)
async def add_card_3(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['card_nickname'] = message.text

    await message.answer(text='Do you confirm?',
                         reply_markup=confirm_kb)

    await AddCard.next()


@dp.message_handler(text='CONFIRM', state=AddCard.confirm)
async def add_card_4(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        await add_card(user_id=message.from_user.id,
                       card_number=data['card_number'],
                       card_nickname=data['card_nickname'])

    await message.answer(text='Confirmed.',
                         reply_markup=start_kb)
    await state.finish()


@dp.message_handler(text='SHOW CARDS')
async def show_cards_nicknames(message: Message) -> None:
    nicks = await get_cards_nicknames(message.from_user.id)

    if not nicks:
        await message.answer(text='There is no card.')
        return

    await message.answer(text='TEST',
                         reply_markup=nickname_kb(nicks))
    await ShowCard.show_card_number.set()


@dp.message_handler(state=ShowCard.show_card_number)
async def show_card_number(message: Message, state: FSMContext) -> None:
    await message.answer(text=f'`{await get_card_number(user_id=message.from_user.id, card_nickname=message.text)}`',
                         parse_mode='markdown',
                         reply_markup=start_kb)
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dispatcher=dp,
                           skip_updates=True,
                           on_startup=on_startup)
