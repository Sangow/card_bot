from contextlib import suppress
from math import ceil
from html import escape
from sqlite3 import IntegrityError

from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, \
    InlineKeyboardMarkup
from aiogram.utils.exceptions import MessageNotModified, TelegramAPIError

from bot.keyboards import main_ikb, about_ikb, cancel_ikb, cards_ikb, \
    card_ikb, edit_ikb, rename_ikb, delete_confirm_ikb, number_taken_ikb
from bot.config import MAX_CARDS, HIDE_AFTER
from bot.sql import add_card, get_cards, get_card, delete_card_by_id, \
    edit_card_by_id, rename_card_by_id, count_cards, nickname_taken, \
    favorite_card_id, set_favorite, unset_favorite, card_with_number
from bot.states import AddCard, ShowCard
from bot.texts import t, get_lang
from .hiding import schedule_hide, cancel_hide
from .service import card_label, format_card_number, nickname_too_long, \
    nickname_looks_like_card_number, normalize_card_number, \
    normalize_card_nickname, MAX_NICKNAME_LENGTH

CARDS_PER_PAGE = 5


async def edit_message(call: CallbackQuery, text: str,
                       reply_markup: InlineKeyboardMarkup,
                       parse_mode: str = None) -> None:
    # Whatever the message shows now, it is no longer the card number that
    # was scheduled to be hidden
    cancel_hide(call.message.chat.id, call.message.message_id)

    # Double taps edit the message to the same content, which Telegram rejects
    with suppress(MessageNotModified):
        await call.message.edit_text(text=text,
                                     parse_mode=parse_mode,
                                     reply_markup=reply_markup)


async def delete_user_message(message: Message) -> None:
    # Inputs are deleted so that card numbers do not stay in the chat
    # history and the flow lives in one bot message. Deleting may fail if
    # the user already deleted the message
    with suppress(TelegramAPIError):
        await message.delete()


async def remember_prompt(state: FSMContext, message_id: int) -> None:
    async with state.proxy() as data:
        data['prompt_id'] = message_id


async def edit_prompt(message: Message, state: FSMContext, text: str,
                      reply_markup: InlineKeyboardMarkup,
                      parse_mode: str = None) -> int:
    """Shows the next step of a text input flow in the message that asked
    for the input, and returns that message's id."""
    async with state.proxy() as data:
        prompt_id = data.get('prompt_id')

    if prompt_id:
        try:
            await message.bot.edit_message_text(text=text,
                                                chat_id=message.chat.id,
                                                message_id=prompt_id,
                                                parse_mode=parse_mode,
                                                reply_markup=reply_markup)
            return prompt_id
        except MessageNotModified:
            return prompt_id
        except TelegramAPIError:
            # The prompt was deleted or can no longer be edited
            pass

    shown = await message.answer(text=text, parse_mode=parse_mode,
                                 reply_markup=reply_markup)
    await remember_prompt(state, shown.message_id)

    return shown.message_id


def card_view_text(lang: str, card_nickname: str, card_number: str) -> str:
    return t(lang, 'card_view',
             nickname=escape(card_nickname),
             number=format_card_number(card_number))


def nickname_error(lang: str, card_nickname: str) -> str:
    if nickname_too_long(card_nickname):
        return t(lang, 'nickname_too_long', limit=MAX_NICKNAME_LENGTH)
    if nickname_looks_like_card_number(card_nickname):
        return t(lang, 'nickname_looks_like_number')

    return t(lang, 'choose_another_nickname')


def help_text(lang: str) -> str:
    return t(lang, 'help', minutes=max(1, round(HIDE_AFTER / 60)))


async def cards_limit_reached(user_id: int) -> bool:
    return await count_cards(user_id=user_id) >= MAX_CARDS


async def cmd_start(message: Message, state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    if await state.get_state():
        await state.finish()

    # Commands are deleted, so the chat keeps only the bot's messages
    await delete_user_message(message)

    # Removes the old reply keyboard for users who still have it
    await message.answer(text=t(lang, 'welcome'),
                         reply_markup=ReplyKeyboardRemove())
    await message.answer(text=t(lang, 'choose_action'),
                         reply_markup=main_ikb(lang))


async def cmd_cancel(message: Message, state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    if await state.get_state():
        await state.finish()

    await delete_user_message(message)

    await message.answer(text=t(lang, 'cancelled'),
                         reply_markup=ReplyKeyboardRemove())
    await message.answer(text=t(lang, 'choose_action'),
                         reply_markup=main_ikb(lang))


async def cmd_cards(message: Message, state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    if await state.get_state():
        await state.finish()

    await delete_user_message(message)

    text, reply_markup = await cards_list(user_id=message.from_user.id,
                                          lang=lang)

    await message.answer(text=text, reply_markup=reply_markup)


async def cmd_add(message: Message, state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    if await state.get_state():
        await state.finish()

    await delete_user_message(message)

    if await cards_limit_reached(user_id=message.from_user.id):
        await message.answer(text=t(lang, 'cards_limit', limit=MAX_CARDS),
                             reply_markup=main_ikb(lang))
        return

    prompt = await message.answer(text=t(lang, 'enter_nickname'),
                                  reply_markup=cancel_ikb(lang))
    await AddCard.card_nickname.set()
    await remember_prompt(state, prompt.message_id)


async def cmd_help(message: Message) -> None:
    lang = get_lang(message.from_user)

    await delete_user_message(message)

    await message.answer(text=help_text(lang), reply_markup=main_ikb(lang))


async def main_menu_handler(call: CallbackQuery, state: FSMContext) -> None:
    lang = get_lang(call.from_user)

    await state.finish()

    await edit_message(call, text=t(lang, 'choose_action'),
                       reply_markup=main_ikb(lang))
    await call.answer()


async def about_handler(call: CallbackQuery) -> None:
    lang = get_lang(call.from_user)

    await edit_message(call, text=help_text(lang),
                       reply_markup=about_ikb(lang))
    await call.answer()


async def dismiss_handler(call: CallbackQuery) -> None:
    # The Read button under an error message removes that message
    with suppress(TelegramAPIError):
        await call.message.delete()
    await call.answer()


async def add_card_1(call: CallbackQuery, state: FSMContext) -> None:
    lang = get_lang(call.from_user)

    await state.finish()

    if await cards_limit_reached(user_id=call.from_user.id):
        await edit_message(call, text=t(lang, 'cards_limit', limit=MAX_CARDS),
                           reply_markup=main_ikb(lang))
        await call.answer()
        return

    await edit_message(call, text=t(lang, 'enter_nickname'),
                       reply_markup=cancel_ikb(lang))
    await AddCard.card_nickname.set()
    await remember_prompt(state, call.message.message_id)
    await call.answer()



async def add_card_2_fail(message: Message, state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    await delete_user_message(message)

    await edit_prompt(message, state,
                      text=nickname_error(lang, message.text),
                      reply_markup=cancel_ikb(lang))


async def add_card_2(message: Message, state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    await delete_user_message(message)

    card_nickname = normalize_card_nickname(message.text)

    if await nickname_taken(user_id=message.from_user.id,
                            card_nickname=card_nickname):
        await edit_prompt(message, state,
                          text=t(lang, 'nickname_not_unique'),
                          reply_markup=cancel_ikb(lang))
        return

    async with state.proxy() as data:
        data['card_nickname'] = card_nickname

    await edit_prompt(message, state, text=t(lang, 'enter_card_number'),
                      reply_markup=cancel_ikb(lang))

    await AddCard.card_number.set()


async def add_card_3_fail(message: Message, state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    await delete_user_message(message)

    await edit_prompt(message, state, text=t(lang, 'card_invalid'),
                      reply_markup=cancel_ikb(lang))


async def add_card_3_not_supported(message: Message,
                                   state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    await delete_user_message(message)

    await edit_prompt(message, state, text=t(lang, 'card_not_supported'),
                      reply_markup=cancel_ikb(lang))


async def add_card_3(message: Message, state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    await delete_user_message(message)

    # Checked again in case several cards were being added at once
    if await cards_limit_reached(user_id=message.from_user.id):
        await edit_prompt(message, state,
                          text=t(lang, 'cards_limit', limit=MAX_CARDS),
                          reply_markup=main_ikb(lang))
        await state.finish()
        return

    card_number = normalize_card_number(message.text)

    # The user stays on this step to enter another number
    duplicate = await card_with_number(user_id=message.from_user.id,
                                       card_number=card_number)
    if duplicate:
        duplicate_id, duplicate_nickname = duplicate
        await edit_prompt(message, state,
                          text=t(lang, 'number_taken',
                                 nickname=duplicate_nickname),
                          reply_markup=number_taken_ikb(duplicate_id,
                                                        duplicate_nickname,
                                                        lang))
        return

    async with state.proxy() as data:
        card_nickname = data['card_nickname']

    try:
        await add_card(user_id=message.from_user.id,
                       card_number=card_number,
                       card_nickname=card_nickname)
    except IntegrityError:
        # Another card got this nickname while the number was being entered
        await edit_prompt(message, state,
                          text=t(lang, 'nickname_not_unique'),
                          reply_markup=cancel_ikb(lang))
        await AddCard.card_nickname.set()
        return

    await edit_prompt(message, state, text=t(lang, 'card_added'),
                      reply_markup=main_ikb(lang))
    await state.finish()

async def cards_list(user_id: int, lang: str,
                     page: int = 0) -> tuple[str, InlineKeyboardMarkup]:
    cards = await get_cards(user_id=user_id)

    if not cards:
        return t(lang, 'no_cards'), main_ikb(lang)

    pages = ceil(len(cards) / CARDS_PER_PAGE)
    # The page may be gone if cards were deleted since the list was shown
    page = min(max(page, 0), pages - 1)
    start = page * CARDS_PER_PAGE

    favorite = await favorite_card_id(user_id=user_id)
    labels = [(card_id, card_label(card_nickname, card_number,
                                   favorite=card_id == favorite))
              for card_id, card_nickname, card_number
              in cards[start:start + CARDS_PER_PAGE]]

    if pages == 1:
        text = t(lang, 'choose_card')
    else:
        text = t(lang, 'choose_card_page', page=page + 1, pages=pages)

    return text, cards_ikb(labels, page, pages, lang)


async def card_page(user_id: int, card_id: int) -> int:
    card_ids = [cid for cid, _, _ in await get_cards(user_id=user_id)]

    if card_id not in card_ids:
        return 0

    return card_ids.index(card_id) // CARDS_PER_PAGE


async def show_cards_handler(call: CallbackQuery,
                             callback_data: dict,
                             state: FSMContext) -> None:
    lang = get_lang(call.from_user)

    await state.finish()

    # The menu button has no page, so it opens the first one
    text, reply_markup = await cards_list(
        user_id=call.from_user.id, lang=lang,
        page=int(callback_data.get('page', 0)))

    await edit_message(call, text=text, reply_markup=reply_markup)
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
    page = await card_page(user_id=call.from_user.id, card_id=card_id)
    favorite = await favorite_card_id(user_id=call.from_user.id) == card_id

    await edit_message(
        call,
        text=card_view_text(lang, card_nickname, card_number),
        parse_mode='html',
        reply_markup=card_ikb(card_id, card_nickname, lang, page, favorite)
    )
    schedule_hide(call.bot, call.message.chat.id, call.message.message_id,
                  card_id, card_nickname, page, lang)
    await call.answer()


async def favorite_handler(call: CallbackQuery,
                           callback_data: dict,
                           state: FSMContext) -> None:
    await set_favorite(user_id=call.from_user.id,
                       card_id=int(callback_data['card_id']))

    # The card view is shown again with the button switched
    await show_card_handler(call, callback_data, state)


async def unfavorite_handler(call: CallbackQuery,
                             callback_data: dict,
                             state: FSMContext) -> None:
    await unset_favorite(user_id=call.from_user.id,
                         card_id=int(callback_data['card_id']))

    await show_card_handler(call, callback_data, state)


async def edit_card_handler(call: CallbackQuery,
                            callback_data: dict,
                            state: FSMContext) -> None:
    lang = get_lang(call.from_user)

    card_id = int(callback_data['card_id'])

    card = await get_card(user_id=call.from_user.id, card_id=card_id)

    # The button may be left in an old message after the card was deleted
    if card is None:
        await call.answer(text=t(lang, 'card_not_found'), show_alert=True)
        return

    card_nickname, card_number = card

    # The card is shown masked, as in the list, so the full number does not
    # stay in the chat while the new one is entered
    await edit_message(call, text=t(lang, 'enter_new_card_number',
                                    card=card_label(card_nickname,
                                                    card_number)),
                       reply_markup=edit_ikb(card_id, lang))

    await ShowCard.edit_card_number.set()
    async with state.proxy() as data:
        data['card_id'] = card_id
        data['prompt_id'] = call.message.message_id

    await call.answer()


async def edit_card_number_fail_handler(message: Message,
                                        state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    async with state.proxy() as data:
        card_id = data['card_id']

    await delete_user_message(message)

    await edit_prompt(message, state, text=t(lang, 'card_invalid'),
                      reply_markup=edit_ikb(card_id, lang))


async def edit_card_number_not_supported_handler(
        message: Message,
        state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    async with state.proxy() as data:
        card_id = data['card_id']

    await delete_user_message(message)

    await edit_prompt(message, state, text=t(lang, 'card_not_supported'),
                      reply_markup=edit_ikb(card_id, lang))


async def edit_card_number_handler(
        message: Message,
        state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    async with state.proxy() as data:
        card_id = data['card_id']

    card_number = normalize_card_number(message.text)

    # The card's own number is allowed, so it can be entered again
    duplicate = await card_with_number(user_id=message.from_user.id,
                                       card_number=card_number,
                                       except_card_id=card_id)
    if duplicate:
        duplicate_id, duplicate_nickname = duplicate
        await delete_user_message(message)
        await edit_prompt(message, state,
                          text=t(lang, 'number_taken',
                                 nickname=duplicate_nickname),
                          reply_markup=number_taken_ikb(
                              duplicate_id, duplicate_nickname, lang,
                              editing_card_id=card_id))
        return

    saved = await edit_card_by_id(
        user_id=message.from_user.id,
        card_id=card_id,
        new_card_number=card_number)

    await delete_user_message(message)

    # The card may have been deleted while the new number was being entered
    if not saved:
        await edit_prompt(message, state, text=t(lang, 'card_not_found'),
                          reply_markup=main_ikb(lang))
        await state.finish()
        return

    await edit_prompt(message, state, text=t(lang, 'info_saved'),
                      reply_markup=main_ikb(lang))
    await state.finish()


async def rename_card_handler(call: CallbackQuery,
                              callback_data: dict,
                              state: FSMContext) -> None:
    lang = get_lang(call.from_user)

    card_id = int(callback_data['card_id'])

    card = await get_card(user_id=call.from_user.id, card_id=card_id)

    # The button may be left in an old message after the card was deleted
    if card is None:
        await call.answer(text=t(lang, 'card_not_found'), show_alert=True)
        return

    card_nickname, _ = card

    # The current nickname shows which card is being renamed
    await edit_message(call, text=t(lang, 'enter_new_nickname',
                                    nickname=card_nickname),
                       reply_markup=rename_ikb(card_id, lang))

    await ShowCard.edit_card_nickname.set()
    async with state.proxy() as data:
        data['card_id'] = card_id
        data['prompt_id'] = call.message.message_id

    await call.answer()


async def rename_card_fail_handler(message: Message,
                                   state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    async with state.proxy() as data:
        card_id = data['card_id']

    await delete_user_message(message)

    await edit_prompt(message, state,
                      text=nickname_error(lang, message.text),
                      reply_markup=rename_ikb(card_id, lang))


async def rename_card_save_handler(message: Message,
                                   state: FSMContext) -> None:
    lang = get_lang(message.from_user)

    async with state.proxy() as data:
        card_id = data['card_id']

    await delete_user_message(message)

    card_nickname = normalize_card_nickname(message.text)

    # The card's own nickname is allowed, so its case can be changed
    if await nickname_taken(user_id=message.from_user.id,
                            card_nickname=card_nickname,
                            except_card_id=card_id):
        await edit_prompt(message, state,
                          text=t(lang, 'nickname_not_unique'),
                          reply_markup=rename_ikb(card_id, lang))
        return

    try:
        await rename_card_by_id(user_id=message.from_user.id,
                                card_id=card_id,
                                new_card_nickname=card_nickname)
    except IntegrityError:
        await edit_prompt(message, state,
                          text=t(lang, 'nickname_not_unique'),
                          reply_markup=rename_ikb(card_id, lang))
        return

    card = await get_card(user_id=message.from_user.id, card_id=card_id)

    if card is None:
        await edit_prompt(message, state, text=t(lang, 'card_not_found'),
                          reply_markup=main_ikb(lang))
        await state.finish()
        return

    card_nickname, card_number = card
    page = await card_page(user_id=message.from_user.id, card_id=card_id)
    favorite = await favorite_card_id(user_id=message.from_user.id) == card_id

    shown_id = await edit_prompt(
        message, state,
        text=card_view_text(lang, card_nickname, card_number),
        parse_mode='html',
        reply_markup=card_ikb(card_id, card_nickname, lang, page, favorite)
    )
    schedule_hide(message.bot, message.chat.id, shown_id,
                  card_id, card_nickname, page, lang)
    await state.finish()


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
