from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards import start_kb, cancel_kb, confirm_kb, nickname_kb, delete_edit_inline_kb
from bot.sql import get_cards_nicknames, add_card, get_card_number, delete_card, edit_card
from bot.states import AddCard, ShowCard


async def cmd_start(message: Message, state: FSMContext) -> None:
    if await state.get_state():
        await state.finish()

    await message.answer(text='Choose button:',
                         reply_markup=start_kb)


async def cmd_cancel(message: Message, state: FSMContext) -> None:
    if await state.get_state():
        await state.finish()

    await message.answer(text='Cancelled.',
                         reply_markup=start_kb)


async def add_card_1(message: Message) -> None:
    await message.answer(text='Enter card number:',
                         reply_markup=cancel_kb)
    await AddCard.card_number.set()


async def add_card_2_fail(message: Message) -> None:
    await message.answer(text='Credit card is invalid.')


async def add_card_2(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['card_number'] = message.text

    await message.answer(text='Enter card nickname (without spaces):')

    await AddCard.next()


async def add_card_3_fail(message: Message) -> None:
    await message.answer('Choose another nickname (without spaces):')


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
            await message.answer(text='Nickname of your card should be unique.\n'
                                      'Choose another nickname (without spaces):',
                                 reply_markup=cancel_kb)
            await AddCard.card_nickname.set()
            return

    await message.answer(text='Confirmed.',
                         reply_markup=start_kb)
    await state.finish()


async def show_cards_nicknames(message: Message) -> None:
    nicks = await get_cards_nicknames(user_id=message.from_user.id)

    if not nicks:
        await message.answer(text='There is no card.')
        return

    await message.answer(text='Choose your card:',
                         reply_markup=nickname_kb(nicks))

    await ShowCard.show_card_number.set()


async def show_card_number(message: Message, state: FSMContext) -> None:
    # print(await get_card_number(user_id=message.from_user.id, card_nickname=message.text))
    # print(message.text.strip())
    await message.answer(text=f'<b>Nickname:</b> {message.text}\n\n'
                              f'⬇️<b>Tap to copy</b>⬇️\n\n'
                              f'<code>{await get_card_number(user_id=message.from_user.id, card_nickname=message.text)}</code>\n\n'
                              f'⬆️<b>Tap to copy</b>⬆️',
                         parse_mode='html',
                         reply_markup=delete_edit_inline_kb)

    # await message.answer(text=f'`{await get_card_number(user_id=message.from_user.id, card_nickname=message.text)}`',
    #                      parse_mode='markdown',
    #                      reply_markup=delete_edit_inline_kb)

    await message.answer(text='Choose button:',
                         reply_markup=start_kb)

    await state.finish()


async def callback_delete(callback: CallbackQuery) -> None:
    await delete_card(user_id=callback.from_user.id,
                      card_nickname=callback.message.text.split()[1])
    await callback.answer(text=f'Card deleted.')
    await callback.message.delete()


async def callback_edit(callback: CallbackQuery) -> None:
    await callback.answer(callback.message.text)
