from contextlib import suppress

from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, \
    InlineKeyboardMarkup
from aiogram.utils.exceptions import MessageNotModified

from bot.keyboards import main_ikb, cancel_ikb, cards_ikb, card_ikb, edit_ikb, \
    delete_confirm_ikb
from bot.sql import add_card, get_cards, get_card, delete_card_by_id, \
    edit_card_by_id
from bot.states import AddCard, ShowCard


async def edit_message(call: CallbackQuery, text: str,
                       reply_markup: InlineKeyboardMarkup,
                       parse_mode: str = None) -> None:
    # Double taps edit the message to the same content, which Telegram rejects
    with suppress(MessageNotModified):
        await call.message.edit_text(text=text,
                                     parse_mode=parse_mode,
                                     reply_markup=reply_markup)


async def cmd_start(message: Message, state: FSMContext) -> None:
    if await state.get_state():
        await state.finish()

    # Removes the old reply keyboard for users who still have it
    await message.answer(text='Welcome to card bot!',
                         reply_markup=ReplyKeyboardRemove())
    await message.answer(text='Choose an action:', reply_markup=main_ikb)


async def cmd_cancel(message: Message, state: FSMContext) -> None:
    if await state.get_state():
        await state.finish()

    await message.answer(text='Cancelled.',
                         reply_markup=ReplyKeyboardRemove())
    await message.answer(text='Choose an action:', reply_markup=main_ikb)


async def main_menu_handler(call: CallbackQuery, state: FSMContext) -> None:
    await state.finish()

    await edit_message(call, text='Choose an action:', reply_markup=main_ikb)
    await call.answer()


async def add_card_1(call: CallbackQuery, state: FSMContext) -> None:
    await state.finish()

    await edit_message(call, text='Enter card number:',
                       reply_markup=cancel_ikb)
    await AddCard.card_number.set()
    await call.answer()


async def add_card_2_fail(message: Message) -> None:
    await message.answer(text='Credit card is invalid.',
                         reply_markup=cancel_ikb)


async def add_card_2(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['card_number'] = message.text.replace(' ', '')

    await message.answer(text='Enter card nickname (without spaces):',
                         reply_markup=cancel_ikb)

    await AddCard.next()


async def add_card_3_fail(message: Message) -> None:
    await message.answer(text='Choose another nickname (without spaces):',
                         reply_markup=cancel_ikb)


async def add_card_3(message: Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        try:
            await add_card(user_id=message.from_user.id,
                           card_number=data['card_number'],
                           card_nickname=message.text)
        except:
            await message.answer(
                text='Nickname of your card should be unique.\n'
                     'Choose another nickname (without spaces):',
                reply_markup=cancel_ikb
            )
            return

    await message.answer(text='Card added.',
                         reply_markup=main_ikb)
    await state.finish()


async def show_cards_handler(call: CallbackQuery, state: FSMContext) -> None:
    await state.finish()

    cards = await get_cards(user_id=call.from_user.id)

    if not cards:
        await edit_message(call, text='There is no card.',
                           reply_markup=main_ikb)
    else:
        await edit_message(call, text='Choose your card:',
                           reply_markup=cards_ikb(cards))

    await call.answer()


async def show_card_handler(call: CallbackQuery,
                            callback_data: dict,
                            state: FSMContext) -> None:
    await state.finish()

    card_id = int(callback_data['card_id'])
    card = await get_card(user_id=call.from_user.id, card_id=card_id)

    if card is None:
        await call.answer(text='Card not found.', show_alert=True)
        return

    card_nickname, card_number = card

    await edit_message(
        call,
        text=f'<b>Nickname:</b> {card_nickname}\n\n'
             f'⬇️<b>Tap to copy</b>⬇️\n\n'
             f'<code>{card_number}</code>\n\n'
             f'⬆️<b>Tap to copy</b>⬆️',
        parse_mode='html',
        reply_markup=card_ikb(card_id)
    )
    await call.answer()


async def edit_card_handler(call: CallbackQuery,
                            callback_data: dict,
                            state: FSMContext) -> None:
    card_id = int(callback_data['card_id'])

    await edit_message(call, text='Enter new card number:',
                       reply_markup=edit_ikb(card_id))

    await ShowCard.edit_card_number.set()
    async with state.proxy() as data:
        data['card_id'] = card_id

    await call.answer()


async def edit_card_number_fail_handler(message: Message,
                                        state: FSMContext) -> None:
    async with state.proxy() as data:
        card_id = data['card_id']

    await message.answer(text='Credit card is invalid.',
                         reply_markup=edit_ikb(card_id))


async def edit_card_number_handler(
        message: Message,
        state: FSMContext) -> None:
    async with state.proxy() as data:
        await edit_card_by_id(user_id=message.from_user.id,
                              card_id=data['card_id'],
                              new_card_number=message.text.replace(' ', ''))

    await message.answer(text='Information saved.',
                         reply_markup=main_ikb)
    await state.finish()


async def confirm_delete_card_handler(call: CallbackQuery,
                                      callback_data: dict,
                                      state: FSMContext) -> None:
    await state.finish()

    card_id = int(callback_data['card_id'])
    card = await get_card(user_id=call.from_user.id, card_id=card_id)

    if card is None:
        await call.answer(text='Card not found.', show_alert=True)
        return

    card_nickname, _ = card

    await edit_message(call, text=f'Delete card "{card_nickname}"?',
                       reply_markup=delete_confirm_ikb(card_id))
    await call.answer()


async def delete_card_handler(call: CallbackQuery,
                              callback_data: dict,
                              state: FSMContext) -> None:
    await state.finish()

    await delete_card_by_id(user_id=call.from_user.id,
                            card_id=int(callback_data['card_id']))

    await edit_message(call, text='Card deleted.', reply_markup=main_ikb)
    await call.answer()
