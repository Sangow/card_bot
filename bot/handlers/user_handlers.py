from contextlib import suppress
from html import escape
from sqlite3 import IntegrityError

from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, \
    InlineKeyboardMarkup
from aiogram.utils.exceptions import MessageNotModified

from bot.keyboards import main_ikb, cancel_ikb, cards_ikb, card_ikb, edit_ikb, \
    rename_ikb, delete_confirm_ikb
from bot.sql import add_card, get_cards, get_card, delete_card_by_id, \
    edit_card_by_id, rename_card_by_id
from bot.states import AddCard, ShowCard
from bot.texts import t, get_lang
from .service import card_label, format_card_number


async def edit_message(call: CallbackQuery, text: str,
                       reply_markup: InlineKeyboardMarkup,
                       parse_mode: str = None) -> None:
    # Double taps edit the message to the same content, which Telegram rejects
    with suppress(MessageNotModified):
        await call.message.edit_text(text=text,
                                     parse_mode=parse_mode,
                                     reply_markup=reply_markup)


def card_view_text(lang: str, card_nickname: str, card_number: str) -> str:
    return t(lang, 'card_view',
             nickname=escape(card_nickname),
             number=format_card_number(card_number))


async def cmd_start(message: Message, state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    if await state.get_state():
        await state.finish()

    # Removes the old reply keyboard for users who still have it
    await message.answer(text=t(lang, 'welcome'),
                         reply_markup=ReplyKeyboardRemove())
    await message.answer(text=t(lang, 'choose_action'),
                         reply_markup=main_ikb(lang))


async def cmd_cancel(message: Message, state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    if await state.get_state():
        await state.finish()

    await message.answer(text=t(lang, 'cancelled'),
                         reply_markup=ReplyKeyboardRemove())
    await message.answer(text=t(lang, 'choose_action'),
                         reply_markup=main_ikb(lang))


async def main_menu_handler(call: CallbackQuery, state: FSMContext) -> None:
    lang = get_lang(call.from_user)

    await state.finish()

    await edit_message(call, text=t(lang, 'choose_action'),
                       reply_markup=main_ikb(lang))
    await call.answer()


async def add_card_1(call: CallbackQuery, state: FSMContext) -> None:
    lang = get_lang(call.from_user)

    await state.finish()

    await edit_message(call, text=t(lang, 'enter_card_number'),
                       reply_markup=cancel_ikb(lang))
    await AddCard.card_number.set()
    await call.answer()


async def add_card_2_fail(message: Message) -> None:
    lang = get_lang(message.from_user)

    await message.answer(text=t(lang, 'card_invalid'),
                         reply_markup=cancel_ikb(lang))


async def add_card_2(message: Message, state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    async with state.proxy() as data:
        data['card_number'] = message.text.replace(' ', '')

    await message.answer(text=t(lang, 'enter_nickname'),
                         reply_markup=cancel_ikb(lang))

    await AddCard.next()


async def add_card_3_fail(message: Message) -> None:
    lang = get_lang(message.from_user)

    await message.answer(text=t(lang, 'choose_another_nickname'),
                         reply_markup=cancel_ikb(lang))


async def add_card_3(message: Message, state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    async with state.proxy() as data:
        try:
            await add_card(user_id=message.from_user.id,
                           card_number=data['card_number'],
                           card_nickname=message.text)
        except IntegrityError:
            await message.answer(
                text=t(lang, 'nickname_not_unique'),
                reply_markup=cancel_ikb(lang)
            )
            return

    await message.answer(text=t(lang, 'card_added'),
                         reply_markup=main_ikb(lang))
    await state.finish()


async def show_cards_handler(call: CallbackQuery, state: FSMContext) -> None:
    lang = get_lang(call.from_user)

    await state.finish()

    cards = [(card_id, card_label(card_nickname, card_number))
             for card_id, card_nickname, card_number
             in await get_cards(user_id=call.from_user.id)]

    if not cards:
        await edit_message(call, text=t(lang, 'no_cards'),
                           reply_markup=main_ikb(lang))
    else:
        await edit_message(call, text=t(lang, 'choose_card'),
                           reply_markup=cards_ikb(cards, lang))

    await call.answer()


async def show_card_handler(call: CallbackQuery,
                            callback_data: dict,
                            state: FSMContext) -> None:
    lang = get_lang(call.from_user)

    await state.finish()

    card_id = int(callback_data['card_id'])
    card = await get_card(user_id=call.from_user.id, card_id=card_id)

    if card is None:
        await call.answer(text=t(lang, 'card_not_found'), show_alert=True)
        return

    card_nickname, card_number = card

    await edit_message(
        call,
        text=card_view_text(lang, card_nickname, card_number),
        parse_mode='html',
        reply_markup=card_ikb(card_id, lang)
    )
    await call.answer()


async def edit_card_handler(call: CallbackQuery,
                            callback_data: dict,
                            state: FSMContext) -> None:
    lang = get_lang(call.from_user)

    card_id = int(callback_data['card_id'])

    await edit_message(call, text=t(lang, 'enter_new_card_number'),
                       reply_markup=edit_ikb(card_id, lang))

    await ShowCard.edit_card_number.set()
    async with state.proxy() as data:
        data['card_id'] = card_id

    await call.answer()


async def edit_card_number_fail_handler(message: Message,
                                        state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    async with state.proxy() as data:
        card_id = data['card_id']

    await message.answer(text=t(lang, 'card_invalid'),
                         reply_markup=edit_ikb(card_id, lang))


async def edit_card_number_handler(
        message: Message,
        state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    async with state.proxy() as data:
        await edit_card_by_id(user_id=message.from_user.id,
                              card_id=data['card_id'],
                              new_card_number=message.text.replace(' ', ''))

    await message.answer(text=t(lang, 'info_saved'),
                         reply_markup=main_ikb(lang))
    await state.finish()


async def rename_card_handler(call: CallbackQuery,
                              callback_data: dict,
                              state: FSMContext) -> None:
    lang = get_lang(call.from_user)

    card_id = int(callback_data['card_id'])

    await edit_message(call, text=t(lang, 'enter_new_nickname'),
                       reply_markup=rename_ikb(card_id, lang))

    await ShowCard.edit_card_nickname.set()
    async with state.proxy() as data:
        data['card_id'] = card_id

    await call.answer()


async def rename_card_fail_handler(message: Message,
                                   state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    async with state.proxy() as data:
        card_id = data['card_id']

    await message.answer(text=t(lang, 'choose_another_nickname'),
                         reply_markup=rename_ikb(card_id, lang))


async def rename_card_save_handler(message: Message,
                                   state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    async with state.proxy() as data:
        card_id = data['card_id']

    try:
        await rename_card_by_id(user_id=message.from_user.id,
                                card_id=card_id,
                                new_card_nickname=message.text)
    except IntegrityError:
        await message.answer(text=t(lang, 'nickname_not_unique'),
                             reply_markup=rename_ikb(card_id, lang))
        return

    await state.finish()

    card = await get_card(user_id=message.from_user.id, card_id=card_id)

    if card is None:
        await message.answer(text=t(lang, 'card_not_found'),
                             reply_markup=main_ikb(lang))
        return

    card_nickname, card_number = card

    await message.answer(text=card_view_text(lang, card_nickname, card_number),
                         parse_mode='html',
                         reply_markup=card_ikb(card_id, lang))


async def confirm_delete_card_handler(call: CallbackQuery,
                                      callback_data: dict,
                                      state: FSMContext) -> None:
    lang = get_lang(call.from_user)

    await state.finish()

    card_id = int(callback_data['card_id'])
    card = await get_card(user_id=call.from_user.id, card_id=card_id)

    if card is None:
        await call.answer(text=t(lang, 'card_not_found'), show_alert=True)
        return

    card_nickname, _ = card

    await edit_message(call,
                       text=t(lang, 'delete_confirm', nickname=card_nickname),
                       reply_markup=delete_confirm_ikb(card_id, lang))
    await call.answer()


async def delete_card_handler(call: CallbackQuery,
                              callback_data: dict,
                              state: FSMContext) -> None:
    lang = get_lang(call.from_user)

    await state.finish()

    await delete_card_by_id(user_id=call.from_user.id,
                            card_id=int(callback_data['card_id']))

    await edit_message(call, text=t(lang, 'card_deleted'),
                       reply_markup=main_ikb(lang))
    await call.answer()
