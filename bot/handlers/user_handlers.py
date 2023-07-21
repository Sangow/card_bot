from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards import start_kb, cancel_kb, confirm_kb, nickname_kb, delete_edit_inline_kb
from bot.sql import get_cards_nicknames, add_card, get_card_number, delete_card
from bot.states import AddCard, ShowCard
from .service import validate_card_number


async def cmd_start(message: Message) -> None:
    await message.answer(text='Choose button:',
                         reply_markup=start_kb)


async def cmd_cancel(message: Message, state: FSMContext) -> None:
    if not await state.get_state():
        await message.answer(text='Cancelled.',
                             reply_markup=start_kb)
        return

    await state.finish()

    await message.answer(text='Cancelled.',
                         reply_markup=start_kb)


async def add_card_1(message: Message) -> None:
    await message.answer(text='Enter card number:',
                         reply_markup=cancel_kb)
    await AddCard.card_number.set()


async def add_card_2(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        if not validate_card_number(message.text):
            await message.answer(text='Credit card is invalid.')
            return
        data['card_number'] = message.text

    await message.answer(text='Enter card nickname:')

    await AddCard.next()


async def add_card_3(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['card_nickname'] = message.text

    await message.answer(text='Do you confirm?',
                         reply_markup=confirm_kb)

    await AddCard.next()


async def add_card_4(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        try:
            await add_card(user_id=message.from_user.id,
                           card_number=data['card_number'],
                           card_nickname=data['card_nickname'])
        except:
            await message.answer(text='Choose another nickname:',
                                 reply_markup=cancel_kb)
            await AddCard.card_nickname.set()
            return

    await message.answer(text='Confirmed.',
                         reply_markup=start_kb)
    await state.finish()


async def show_cards_nicknames(message: Message) -> None:
    nicks = await get_cards_nicknames(message.from_user.id)

    if not nicks:
        await message.answer(text='There is no card.')
        return

    await message.answer(text='Choose your card:',
                         reply_markup=nickname_kb(nicks))

    await ShowCard.show_card_number.set()


async def show_card_number(message: Message, state: FSMContext) -> None:
    await message.answer(text=f'`{await get_card_number(user_id=message.from_user.id, card_nickname=message.text)}`',
                         parse_mode='markdown',
                         reply_markup=delete_edit_inline_kb)

    await message.answer(text='Choose button:',
                         reply_markup=start_kb)

    await state.finish()


async def callback_delete(callback: CallbackQuery) -> None:
    await delete_card(user_id=callback.from_user.id,
                      card_number=callback.message.text)
    await callback.answer(text='Card deleted.')
    await callback.message.delete()


async def callback_edit(callback: CallbackQuery) -> None:
    await callback.answer(text='In process... ^-^')
